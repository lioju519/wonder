from flask import Flask, render_template, url_for, request, make_response, redirect, Response, Blueprint, session
from . import gestion_salidas
from ast import dump
import datetime
from operator import index
from socket import IPV6_DONTFRAG
import time
from datetime import datetime
import os
from werkzeug.utils import secure_filename
from werkzeug.datastructures import  FileStorage
import flask
from flask.helpers import flash
from numpy import append
import sqlalchemy
from sqlalchemy.engine import URL
from sqlalchemy import create_engine
import pymysql
from . bd import obtener_conexion
import json
import mysql.connector
from mysql import connector
import pandas as pd
import csv
import sqlite3
import xlrd
import io
import xlwt
from flask_mail import Mail, Message
from datetime import datetime, date


@gestion_salidas.route('/gestion')
def gestion():
    
    conexion=obtener_conexion()
    with conexion.cursor() as cursor:
        number_of_rows = cursor.execute('SELECT * FROM cargues')
         
    return render_template('gestion.html', datos = number_of_rows)

#cargar salidas 1
@gestion_salidas.route('/cargar')
def cargar():
  
    reiniciarCargue()
    cargue_activo = 0
    conexion=obtener_conexion()
    with conexion.cursor() as cursor:
        cursor.execute("SELECT * FROM cargues")
        result_set = cursor.fetchall()
    
    if result_set:

        cargue_activo = 1

        print('modal indicando que ya hay datos en la tabla validar')
        flash("Ya existen datos en la tabla 'cargues'", 'Validar')
        return render_template('gestion.html', cargue_activo = cargue_activo, result_set = result_set) 
    else:
        db = 'inventario'
        table = 'cargues'
        path = "C:/python/cargas_salidas.xlsm"

        url = "mysql+mysqlconnector://root:@localhost/"
        engine = create_engine(url + db)
        df = pd.read_excel(path)
        df.to_sql(name = table, con = engine, if_exists='append', index= False)

        cal()

        flash("VENTAS CARGADAS CORRECTAMENTE")
        return render_template('gestion.html')

#funcion reiniciar cargue
def reiniciarCargue():

    conexion = obtener_conexion()
    with conexion.cursor() as cursor:
        cursor.execute('UPDATE historial_cargues_ventas SET control_cargue = 0')
        conexion.commit()
    return None

#funcion limpiar cargue
def limpiarCargue():

    conexion = obtener_conexion()
    with conexion.cursor() as cursor:
        cursor.execute("DELETE FROM cargues WHERE order_id = ''")
        conexion.commit()

        cursor.execute("DELETE FROM historial_cargues_ventas WHERE order_id = ''")
        conexion.commit()
    return None

#validar cargue 2
@gestion_salidas.route('/validaCargue')
def validaCargue():

    limpiarCargue()

    conexion=obtener_conexion()
    with conexion.cursor() as cursor:
        cursor.execute("SELECT id, sku FROM cargues")
        data = result_set = cursor.fetchall()
        #print(data)
        cont = 1
        faltantes = []
        for x in data:
            #print(x[1])
            cursor.execute('SELECT sku_padre FROM productos WHERE sku_padre = %s',x[1])
            data_2 = result_set = cursor.fetchall()
            
            if(data_2):
                print('ok', x[1])
                print('')

            else:
                #print(x[1])
                faltantes.append(x[1]) 
        #print(faltantes)
                        
            #flash("CARGUE GESTIONADO CORRECTAMENTE")        
    
        return render_template('validaCargue.html',faltantes_1 = faltantes) 

@gestion_salidas.route('/validaTablaCargue')
def validaTablaCargue():
    conexion=obtener_conexion()
    with conexion.cursor() as cursor:
        cursor.execute("SELECT id, order_id, sku, cant_v, fecha  FROM cargues")
        data = result_set = cursor.fetchall()
        for x in data:
            order_id = x[1]
            sku = x[2]
            cant_v = [3]
            fecha = x[4]
            #print(order_id)
            cursor.execute('SELECT id FROM historial_cargues_ventas WHERE order_id = %s',x[1])
            data_2 = result_set = cursor.fetchall()
            
            if(data_2):
                #print(x[0])
                cursor.execute("DELETE FROM cargues WHERE order_id = %s",x[1])
                conexion.commit()
            
            else:
              print('ok')

        with conexion.cursor() as cursor:
            cursor.execute("SELECT c.sku_indivisible, c.total_venta, i.cantidad as qty_actual, i.cantidad - c.total_venta AS qty_final FROM computo_salidas c INNER JOIN inventario i ON(c.sku_indivisible = i.sku_indivisible)")
            data_consolidado = result_set = cursor.fetchall()

        with conexion.cursor() as cursor:
            cursor.execute("SELECT SUM(cantidad) FROM inventario")
            data_actual_inventario = result_set = cursor.fetchone()

        with conexion.cursor() as cursor:
            cursor.execute("SELECT SUM(total_venta) FROM computo_salidas")
            data_carga = result_set = cursor.fetchone()

        inventario_antes = data_actual_inventario[0]
        data_carga_total = data_carga[0]
        
        total_despues = int(inventario_antes) - int(data_carga_total)

        fecha_hora_actual = datetime.now()

        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            cursor.execute("INSERT INTO qty_ingreso_antes (qty_carga,qty_inventario,qty_final,fecha) VALUES (%s,%s,%s,%s)",(data_carga_total,inventario_antes,total_despues,fecha_hora_actual))
            conexion.commit()
        
        with conexion.cursor() as cursor:
            cursor.execute("SELECT * FROM qty_ingreso_antes")
            data_calculo_antes = result_set = cursor.fetchall()
        

    return render_template('gestion.html', data_consolidado = data_consolidado, data_calculo_antes = data_calculo_antes)

@gestion_salidas.route('/ventas')
def ventas():
    conexion=obtener_conexion()
    with conexion.cursor() as cursor:
        
        cursor.execute("SELECT p.sku_indivisible, p.cantidad, c.cant_v, p.cantidad * c.cant_v as total, c.order_id, c.fecha as fecha, c.sku, p.tipo_producto, c.nombre_corto_sku, c.destinatario, c.estado FROM productos p  INNER JOIN cargues c on (p.sku_padre = c.sku)")
        data = result_set = cursor.fetchall()

        for x in data:
            tipo_combo = x[7]
            order_id = x[4]
            fecha = x[5]
            nombre_corto_sku = x[8]
            destinatario = x[9]
            estado_2 = x[10]
            #print(x[7])
            if(tipo_combo=='COMBO'):
                
                sku_combo = x[6]
                cantidad_vendida_combos = int(x[2])
               # print(sku_combo)
               #sku_indivisibles del combo
                with conexion.cursor() as cursor:
                    cursor.execute('SELECT sku_indivisible FROM combos WHERE sku_combo = %s',sku_combo)
                    result_set = cursor.fetchall()
                #print(result_set)
                for i in result_set:

                    #se recorren y se saca la cantidad
                    #print(i[0])
                    with conexion.cursor() as cursor:
                        cursor.execute('SELECT sku_indivisible,sku_padre, cantidad FROM productos WHERE sku_padre = %s',i[0])
                        result_set_2 = cursor.fetchone()
                    #cantidad tabla producto
                    cantidad_producto = int(result_set_2[2])
                    #sku indivisible para restar
                    sku_indivisible_2 = result_set_2[0]
                    with conexion.cursor() as cursor:
                        cursor.execute('SELECT  cantidad FROM inventario WHERE sku_indivisible = %s',sku_indivisible_2)
                        result_set_3 = cursor.fetchone()
                    #cantidad inventario
                    cantidad_inventario = int(result_set_3[0])

                    total = cantidad_inventario  - (cantidad_producto * cantidad_vendida_combos) 

                    #falta probar la consulta, cambiar valores de la tabla inventario
                    conexion = obtener_conexion()
                    with conexion.cursor() as cursor:
                        cursor.execute('UPDATE inventario SET cantidad = %s WHERE sku_indivisible = %s',(total, sku_indivisible_2))
                        conexion.commit()
                    
                conexion = obtener_conexion()
                with conexion.cursor() as cursor:
                    cursor.execute("INSERT INTO historial_cargues_ventas (order_id,sku,nombre_corto_sku, cant_v,destinatario,fecha, tipo_producto,estado_2) VALUES (%s,%s,%s,%s,%s,%s,'COMBO',%s)",(order_id,sku_combo,nombre_corto_sku,cantidad_vendida_combos,destinatario,fecha,estado_2))
                    conexion.commit()

            else:
                conexion = obtener_conexion()
                with conexion.cursor() as cursor:
                    cursor.execute('SELECT cantidad FROM inventario WHERE sku_indivisible = %s',x[0])
                    result_set = cursor.fetchall()
                
                for j in result_set:
                    total_2 = j[0] - x[3]
                    sku_3 = x[0]

                    cantidad_v = x[2]
                    
                    order = x[4]
                    fecha = x[5]
                    sku = x[6]

                    conexion = obtener_conexion()
                    with conexion.cursor() as cursor:
                        cursor.execute("UPDATE inventario SET cantidad = %s WHERE sku_indivisible = %s",(total_2,sku_3))
                        conexion.commit()
                    print(estado_2)
                    conexion = obtener_conexion()
                    with conexion.cursor() as cursor:
                        cursor.execute("INSERT INTO historial_cargues_ventas (order_id,sku,nombre_corto_sku, cant_v,destinatario,fecha,estado_2) VALUES (%s,%s,%s,%s,%s,%s,%s)",(order_id,sku,nombre_corto_sku,cantidad_v,destinatario,fecha,estado_2))
                        conexion.commit()
                #funcion para dejar los valores negativos en 0 despues de ralizar el cargue
                  
                print('entra normales')
        #dejarCero() 
        flash("CARGUE GESTIONADO CORRECTAMENTE")
        return render_template('gestion.html')

#borrar cargue al finalizar
@gestion_salidas.route('/borrar_cargue')
def borrar_cargue():
    conexion=obtener_conexion()
    with conexion.cursor() as cursor:
        cursor.execute("TRUNCATE TABLE cargues")
        conexion.commit()
    
    with conexion.cursor() as cursor:
        cursor.execute("TRUNCATE TABLE computo_salidas")
        conexion.commit()
    
    with conexion.cursor() as cursor:
        cursor.execute("TRUNCATE TABLE qty_ingreso_antes")
        conexion.commit()
        
    with conexion.cursor() as cursor:
        cursor.execute("TRUNCATE TABLE envio_correo")
        conexion.commit()

        flash("TABLA BORRADA CORRECTAMENTE CORRECTAMENTE")
        return render_template('gestion.html')

@gestion_salidas.route('/ventas1_1',methods=['POST','GET'])
def ventas1_1():

    no_orden = request.form['no_orden']
    sku_indivisible = request.form['sku_indivisible']
    sku = request.form['sku']
    cantidad_v = request.form['cantidad_v']
    fecha = request.form['fecha']
   
    conexion=obtener_conexion()
    with conexion.cursor() as cursor:

        cursor.execute("SELECT p.sku_indivisible, p.cantidad, c.cant_v, p.cantidad * c.cant_v as total FROM productos p  INNER JOIN cargues c on (p.sku_padre = c.sku)")

        cursor.execute("SELECT cantidad FROM productos WHERE sku_padre = %s", (sku))
        data = result_set = cursor.fetchone()
        cantidad_producto = data[0]

        cantidad_total_v = cantidad_producto * cantidad_v

        cursor.execute('SELECT cantidad FROM inventario WHERE sku_indivisible = %s',(sku_indivisible))
        data_2 = result_set = cursor.fetchone()
       

        cantidad_invent = data_2[0]

        total = int(cantidad_invent) -  int(cantidad_total_v)

        cursor.execute("UPDATE inventario SET cantidad = %s WHERE sku_indivisible = %s",(total,sku_indivisible))
        conexion.commit()

       
        flash("CARGUE GESTIONADO CORRECTAMENTE")
    return render_template('gestion.html')


#función correos
@gestion_salidas.route('/bucle')
def envioC():
   
    conexion=obtener_conexion()
    with conexion.cursor() as cursor:
        cursor.execute('SELECT  marca FROM envio_correo WHERE marca = 1')
        result_set_marca_1 = cursor.fetchone()
        marca_1 = cursor.rowcount

    conexion=obtener_conexion()
    with conexion.cursor() as cursor:
        cursor.execute('SELECT  marca FROM envio_correo WHERE marca = 0')
        result_set_marca_0 = cursor.fetchone()
    
        marca_0 = cursor.rowcount
    

    if(marca_1 == 0 and marca_0 == 0):

        print('entra si no hay')
        conexion=obtener_conexion()
        with conexion.cursor() as cursor:
            cursor.execute('SELECT email, cod_seguimiento, destinatario, order_id, marca FROM cargues GROUP BY email')
            data_4 = result_set = cursor.fetchall()
            
            for j in data_4:
                email = j[0]
                cod_seguimiento = j[1]
                destinatario = j[2]
                order_id = j[3]
                marca = j[4]

                if(email):
                    conexion = obtener_conexion()
                    with conexion.cursor() as cursor:
                        cursor.execute("INSERT INTO envio_correo (email,cod_seguimiento,destinatario, order_id,marca) VALUES (%s,%s,%s,%s,%s)",(email, cod_seguimiento, destinatario, order_id, marca))
                        conexion.commit()
                else:
                    print('correo no valido')

            pruebaCorreo()
            
            return 'ok cargue correos'
        
    elif(marca_1 >= 1 ):
        #print( marca_1, marca_0)
        pruebaCorreo()  
    
    #ojo borrar cargue sin boton es automatico  
    borrar_cargue()
    flash('CORREOS ENVIADOS CORRECTAMENTE, TOTAL: ' + str(marca_1))
    return render_template('gestion.html')

#@gestion_salidas.route('/bucle2')
def pruebaCorreo():
        
        conexion=obtener_conexion()
        with conexion.cursor() as cursor:
            cursor.execute('SELECT marca FROM envio_correo WHERE marca = 1')
            result_set_marca = cursor.fetchall()
        
        if(result_set_marca):
            
            conexion=obtener_conexion()
            with conexion.cursor() as cursor:
                cursor.execute('SELECT marca, id, cod_seguimiento, email, destinatario, order_id FROM envio_correo WHERE marca = 1')
                result_set = cursor.fetchall()
            
                cantidad_correos = len(result_set)
                
                if(cantidad_correos == 0):
                    print('NO HAY REGISTROS PARA ENVIO')
                    return render_template('gestion.html')
                else:
                    
                    conexion=obtener_conexion()
                    with conexion.cursor() as cursor:
                        cursor.execute('SELECT marca, id, cod_seguimiento, email, destinatario, order_id FROM envio_correo WHERE marca = 1')
                        result_set_2 = cursor.fetchall()
                    
                    for j in result_set_2:

                        id = j[1]
                        email = j[3]
                        codigo_seg = j[2]
                        cliente = j[4]
                        n_orden = j[5]
                        marca = j[0]

                        html_content = '<p>¡Hola! <b>'+ cliente +' </b><br><p>Este es un mensaje de WonderMarket en relación a su pedido <b>'+ n_orden +'</b> realizado con nosotros.<br><br> Le comunicamos que su número de seguimiento es: <b> '+ codigo_seg + '</b><br><br> Correos Express es el transportista encargado de su envío, su link para el seguimiento es https://s.correosexpress.com/<br><br> Esperamos que le pueda llegar en los próximos días hábiles.<br><br>Cualquier incidencia con el envío consulte en la web de Correos Express el estado de su pedido, si no consiguen la entrega contáctenos directamente a los correos o email de la firma.<br><br> ¡Muchas gracias, un saludo!</p>'
                        mail = Mail()

                        msg = Message(
                            subject  = ("Código de seguimiento pedido WonderMarket"), 
                            sender = 'mercado.maravillas.online@gmail.com', 
                            recipients = [email], 
                            html=html_content
                        ) 

                        mail.send(msg)

                        print(email)
                        conexion=obtener_conexion()
                        with conexion.cursor() as cursor:
                            cursor.execute("UPDATE envio_correo SET marca = 0 WHERE id = %s",(id))
                            conexion.commit()
                        
                        
                        time.sleep(10)
                        
                        conexion=obtener_conexion()
                        with conexion.cursor() as cursor:
                            cursor.execute("SELECT * FROM envio_correo WHERE marca = 1")
                            correos_enviados= conexion.commit()
                        
                        #return render_template('gestion.html', correos_enviados = correos_enviados)
                        
        else:
                
            print('NO HAY REGISTROS PARA ENVIO')
            return render_template('gestion.html')


def cal():

    conexion=obtener_conexion()
    with conexion.cursor() as cursor:
        cursor.execute("SELECT p.sku_indivisible, SUM(c.cant_v * p.cantidad) AS total_sum FROM cargues c INNER JOIN productos p ON c.sku = p.sku_padre WHERE p.tipo_producto != 'COMBO' GROUP BY p.sku_indivisible")
        data_agrupados = cursor.fetchall()

        for x in data_agrupados:

            sku_indivisible = x[0]
            total_venta = x[1]

            conexion=obtener_conexion()
            with conexion.cursor() as cursor:
                cursor.execute("INSERT INTO computo_salidas (sku_indivisible, total_venta) VALUES(%s, %s)",(sku_indivisible, total_venta))
                conexion.commit()

    ###
    conexion=obtener_conexion()
    with conexion.cursor() as cursor:
        cursor.execute("SELECT co.sku_indivisible, SUM(c.cant_v * p.cantidad) AS total_sum FROM cargues c INNER JOIN productos p ON c.sku = p.sku_padre INNER JOIN combos co ON c.sku = co.sku_combo WHERE p.tipo_producto = 'COMBO' GROUP BY co.sku_indivisible")
        data_agrupados_combos = cursor.fetchall()

    for y  in data_agrupados_combos:

        sku_indivisible = y[0]
        total_venta = int(y[1])

        conexion=obtener_conexion()
        with conexion.cursor() as cursor:
            cursor.execute("SELECT sku_indivisible, total_venta FROM computo_salidas WHERE sku_indivisible = %s", (sku_indivisible))
            data_repetida_combos = cursor.fetchone()

        if(data_repetida_combos):
            print(sku_indivisible)
            total_venta_1 = int(data_repetida_combos[1])
            
            total = int(total_venta_1) + int(total_venta)
            
            conexion=obtener_conexion()
            with conexion.cursor() as cursor:
                cursor.execute("UPDATE computo_salidas SET total_venta = %s WHERE sku_indivisible = %s",(total, sku_indivisible))
                conexion.commit()

        else:
           
            conexion=obtener_conexion()
            with conexion.cursor() as cursor:
                cursor.execute("INSERT INTO computo_salidas (sku_indivisible, total_venta) VALUES(%s, %s)",(sku_indivisible, total_venta))
                conexion.commit()


    return 'cprueba'

#deja los valores negativos en 0 despues de realizar la gestió de las salidas
def dejarCero():

    cantidad = 0

    conexion=obtener_conexion()
    with conexion.cursor() as cursor:
        cursor.execute("UPDATE inventario SET cantidad = %s WHERE cantidad < %s",(cantidad, cantidad))
        conexion.commit()
    
    return '0'


###DESGLOSE TABLA HISTORIAL VENTAS

@gestion_salidas.route('/desgloseHv')
def calhv():
    conexion = obtener_conexion()

    try:
        with conexion.cursor() as cursor:
            # No combos
            cursor.execute("SELECT c.order_id, p.sku_indivisible, p.sku_padre, (c.cant_v * p.cantidad) AS total_sum, c.fecha, p.tipo_producto, c.estado_2 FROM historial_cargues_ventas c INNER JOIN productos p ON c.sku = p.sku_padre WHERE p.tipo_producto != 'COMBO'")
            data_historial = cursor.fetchall()

            for x in data_historial:
                order_id, sku_indivisible, sku_padre, cant_v, fecha, tipo_producto, estado_2 = x
                tipo_producto = ''

                print(order_id, sku_indivisible, sku_padre, cant_v, fecha, tipo_producto, estado_2)

                cursor.execute("INSERT INTO desglose_historial_ventas (order_id, sku_indivisible, sku_padre, cant_v, fecha, tipo_producto, estado_2) VALUES (%s, %s, %s, %s, %s, %s, %s)", (order_id, sku_indivisible, sku_padre, cant_v, fecha, tipo_producto, estado_2))
        
        # Combos
        with conexion.cursor() as cursor:
            cursor.execute("SELECT c.order_id, co.sku_indivisible, p.sku_padre , (c.cant_v * p.cantidad) AS total_sum, c.fecha, p.tipo_producto, c.estado_2 FROM historial_cargues_ventas c INNER JOIN productos p ON c.sku = p.sku_padre INNER JOIN combos co ON c.sku = co.sku_combo WHERE p.tipo_producto = 'COMBO'")
            data_agrupados_combos = cursor.fetchall()

            cursor.executemany("INSERT INTO desglose_historial_ventas (order_id, sku_indivisible, sku_padre, cant_v, fecha, tipo_producto, estado_2) VALUES(%s, %s, %s, %s, %s, %s, %s)", data_agrupados_combos)
        
        conexion.commit()
        return 'cprueba'

    except pymysql.Error as e:
        print(f"Error de base de datos: {e}")

    finally:
        conexion.close()

 #LOTES SALIDAS

 #VISTA ANTES DE REALIZAR LA SALIDA Y ACTUALIZAR LAS TABLAS HISTOTIAL E INVENTARIO LOTES

@gestion_salidas.route('/vista_lotes')
def vistaLotes():
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute("""
                SELECT p.sku_indivisible, p.sku_padre, p.tipo_producto 
                FROM cargues c 
                INNER JOIN productos p ON c.sku = p.sku_padre 
                INNER JOIN inventario i ON p.sku_indivisible = i.sku_indivisible 
                ORDER BY p.sku_indivisible
            """)
            data_sku_cargue = cursor.fetchall()

        productos = []
        data_sku_combo = []

        for x in data_sku_cargue:
            sku_indivisible = x[0]
            sku_padre = x[1]
            tipo_producto = x[2]

            if tipo_producto == 'COMBO':
                with conexion.cursor() as cursor:
                    cursor.execute("SELECT sku_indivisible FROM combos WHERE sku_combo = %s", (sku_indivisible,))
                    combo_skus = cursor.fetchall()
                    for combo_sku in combo_skus:
                        data_sku_combo.append(combo_sku[0])
            else:
                productos.append(sku_indivisible)

        # Unir las listas productos y data_sku_combo
        all_skus = productos + data_sku_combo

        # Crear una lista para almacenar los resultados de inventario_lotes
        data_historial_lotes_list = []

        for y in all_skus:
            with conexion.cursor() as cursor:
                cursor.execute("SELECT * FROM inventario_lotes WHERE sku_indivisible = %s", (y,))
                data_historial_lotes = cursor.fetchall()

                # Agregar los resultados a la lista
                if data_historial_lotes:
                    for historial in data_historial_lotes:
                        data_historial_lotes_list.append(historial)

        return render_template('vistaLotes.html', all_skus=all_skus, data_historial_lotes=data_historial_lotes_list)
    finally:
        conexion.close()

#funcion para guardar en tabla movimientos sku y en la tabla historial lotes
@gestion_salidas.route('/salidasGuardaHistorialLotes')
def guardaMovimientosSalidaLotes():
    conexion = obtener_conexion()

    try:
        with conexion.cursor() as cursor:
            cursor.execute("""
                SELECT c.order_id, p.sku_indivisible, p.sku_padre, i.cantidad, p.cantidad, c.cant_v, p.precio AS 'Precio Base', p.tipo_producto
                FROM cargues c 
                INNER JOIN productos p ON c.sku = p.sku_padre 
                INNER JOIN inventario i ON p.sku_indivisible = i.sku_indivisible 
                ORDER BY sku_indivisible
            """)
            data_cargue_antes = cursor.fetchall()
            num_registros = len(data_cargue_antes)  # Obtener la cantidad de registros
            #print(f"Número de registros: {num_registros}")
        
            for x in data_cargue_antes:

                tipo_producto = x[7]
                sku_indivisible = x[1]
                sku_padre = x[2]
                
                if tipo_producto == 'COMBO':

                    #print(sku_indivisible, sku_padre)

                    with conexion.cursor() as cursor:
                        cursor.execute("SELECT sku_indivisible FROM combos WHERE sku_combo = %s",(sku_indivisible))
                        data_combos = cursor.fetchall()

                    for j in data_combos:
                        
                        sku_indivisible_combo = j[0]
                        #print(sku_indivisible_combo)
                        validaSkuInventarioLotes(sku_indivisible_combo)

                else:

                    validaSkuInventarioLotes(sku_indivisible)
                
        return 'hola'

    except pymysql.Error as e:
        print(f"Error de base de datos: {e}")

    finally:
        conexion.close()
    
    return 'hola'

"""
FUNCION QUE RECIBE LOS SKU SOLOS DESGLOSADOS EN CASO DE SER COMBO 
Y LOS PROCESA GUARDANDO EN LAS TABLAS QUE CORRESPONDA
"""

def validaSkuInventarioLotes(sku_indivisible):
    print(sku_indivisible, 'ojo')
    conexion = obtener_conexion()
    try:
        movimiento = 'Salida_Antes_Cargue'
        fecha_sistema = datetime.now().date()  # Ensure fecha_sistema is a date object
        usuario = session['usuario']

        with conexion.cursor() as cursor:
            cursor.execute("SELECT * FROM inventario_lotes WHERE sku_indivisible = %s", (sku_indivisible,))
            data_sku_inventario_lotes = cursor.fetchall()
            num_registros_lotes = len(data_sku_inventario_lotes)

        if num_registros_lotes == 0:
            
            with conexion.cursor() as cursor:
                cursor.execute("""
                    SELECT p.fecha_caducidad, i.cantidad, p.precio 
                    FROM productos p 
                    INNER JOIN inventario i ON(p.sku_padre = i.sku_indivisible) 
                    WHERE p.sku_padre = %s
                """, (sku_indivisible,))
                data_sku = cursor.fetchall()

                for x in data_sku:
                    fecha_vencimiento = x[0]  # Extract the correct element from tuple
                    cantidad = x[1]
                    precio = x[2]

                    #print(f"Raw fecha_vencimiento: {fecha_vencimiento}")

                    # Handle invalid date as string
                    if isinstance(fecha_vencimiento, str) and fecha_vencimiento == '0000-00-00':
                        #print("Fecha inválida encontrada: 0000-00-00")
                        fecha_vencimiento = None
                    elif isinstance(fecha_vencimiento, str):
                        # Convert fecha_vencimiento to a date object
                        fecha_vencimiento = datetime.strptime(fecha_vencimiento, '%Y-%m-%d').date()

                    #print(f"Processed fecha_vencimiento: {fecha_vencimiento}")

                    # Ensure fecha_vencimiento is not None before comparison
                    if fecha_vencimiento is not None and fecha_vencimiento <= fecha_sistema:
                        activo = 0
                        print('llega inactivo')
                    else:
                        print('llega activo')
                        activo = 1
                    #print(sku_indivisible)
                    # Guarda nuevo registro en inventario_lotes ya que no existe, esto con los datos de la tabla producto
                    #print(f"sku_indivisible lotes: {sku_indivisible}")
                    with conexion.cursor() as cursor:
                        cursor.execute("INSERT INTO inventario_lotes (sku_indivisible, fecha_vencimiento, cantidad, precio_coste, activo, usuario) VALUES (%s, %s, %s, %s, %s, %s)", (sku_indivisible, fecha_vencimiento, cantidad, precio, activo, usuario))
                        conexion.commit()
                    
                    # Guarda en historial_inventario_lotes lo que se acaba de crear en inventario_lotes
                    with conexion.cursor() as cursor:
                        cursor.execute("INSERT INTO historial_inventario_lotes (sku_indivisible, fecha_vencimiento, cantidad, precio_coste, activo, movimiento, fecha_sistema, usuario) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", (sku_indivisible, fecha_vencimiento, cantidad, precio, activo, movimiento, fecha_sistema, usuario))
                        conexion.commit()

                    #print(sku_indivisible, fecha_vencimiento, cantidad, precio, activo, movimiento, fecha_sistema, usuario)
        else:
            
            with conexion.cursor() as cursor:
                cursor.execute("SELECT sku_indivisible, fecha_vencimiento, cantidad, precio_coste, activo, usuario FROM inventario_lotes WHERE sku_indivisible = %s", (sku_indivisible))
                data_sku_inventario_lotes = cursor.fetchall()
            
            for x in data_sku_inventario_lotes:

                fecha_vencimiento = x[0]
                cantidad = x[1]
                precio = x[2]
                activo = x[3]
                movimiento = 'Salida_Antes_Cargue'
                fecha_sistema = datetime.now().date()  # Ensure fecha_sistema is a date object
                usuario = session['usuario']
            
                # Guarda en historial_inventario_lotes lo que se acaba de crear en inventario_lotes
                with conexion.cursor() as cursor:
                    cursor.execute("INSERT INTO historial_inventario_lotes (sku_indivisible, fecha_vencimiento, cantidad, precio_coste, activo, movimiento, fecha_sistema, usuario) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", (sku_indivisible, fecha_vencimiento, cantidad, precio, activo, movimiento, fecha_sistema, usuario))
                    conexion.commit()

        return 'Hola valida'

    except pymysql.Error as e:
        print(f"Error de base de datos: {e}")
    finally:
        conexion.close()


#FUNCION QUE RECIBE DEL BOTIN LO QUE SE VA A ACTUALIZAR

@gestion_salidas.route('/actualiza-cantidad-lotes', methods=['POST','GET'])
def actualizaCantidadLotes():
    conexion = obtener_conexion()

    try:

        sku_indivisible = request.form['sku_indivisible']
        cantidad = int(request.form['cantidad'])
        id = request.form['id']
        fecha_vencimiento = request.form['fecha_vencimiento']
        fecha_sistema = datetime.now().date()  # Ensure fecha_sistema is a date object
        usuario = session['usuario']
        estado = 'Salida'
        
        print(cantidad)

        if cantidad == 0:
            activo = 0
            movimiento = 'Inactiva_Lote'
            print('entra')
            with conexion.cursor() as cursor:
                cursor.execute('UPDATE inventario_lotes SET cantidad = %s, activo = %s WHERE id = %s', (cantidad, activo ,id))
                conexion.commit()
           

            with conexion.cursor() as cursor:
                cursor.execute("INSERT INTO registro_movimientos_sku (sku_indivisible, cantidad_afectada, activo, estado, movimiento, fecha_vencimiento, fecha_sistema, usuario) VALUES(%s, %s, %s, %s, %s, %s, %s, %s)", (sku_indivisible, cantidad, activo, estado, movimiento, fecha_vencimiento, fecha_sistema, usuario ))
                conexion.commit()
        else:
            
            movimiento = 'Cambio_Qty_Lote'

            print('no entra')
            with conexion.cursor() as cursor:
                cursor.execute('UPDATE inventario_lotes SET cantidad = %s WHERE id = %s', (cantidad, id))
                conexion.commit()

            activo = 1

            with conexion.cursor() as cursor:
                cursor.execute("INSERT INTO registro_movimientos_sku (sku_indivisible, cantidad_afectada, activo, estado, movimiento, fecha_vencimiento, fecha_sistema, usuario) VALUES(%s, %s, %s, %s, %s, %s, %s, %s)", (sku_indivisible, cantidad, activo, estado, movimiento, fecha_vencimiento, fecha_sistema, usuario ))
                conexion.commit()

    except pymysql.Error as e:
         print(f"Error de base de datos: {e}")

    finally:

        conexion.close()

    flash("Cantidad del lote actualizada corresctamente")
    return redirect(request.referrer or url_for('vistaLotes'))