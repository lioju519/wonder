from flask import Flask, render_template, url_for, request, make_response, redirect, Response, Blueprint,send_from_directory, session
import application
from . import excepcion_precio
from ast import dump
from datetime import datetime
from operator import index
from socket import IPV6_DONTFRAG
import time
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

@excepcion_precio.route('/excepcion_precio')
def excepcion():
    
    try:

        conexion=obtener_conexion()
        with conexion.cursor() as cursor:
            cursor.execute('SELECT id, sku_indivisible, precio, fecha, usuario FROM exepciones_precio')
            data_precios = cursor.fetchall()
            #print(data_precios)
    
        return render_template('exepciones.html', data_precios = data_precios)

    except Exception as e:
        # Manejar la excepción aquí, por ejemplo, imprimir un mensaje de error
        print("Ocurrió un error al ejecutar la consulta:", e)
        flash("Ocurrió un error al ejecutar la consulta:", e)
        return redirect(url_for('excepcion_precio.excepcion')) 
        # También puedes revertir la transacción si es necesario
        conexion.rollback()
    finally:
        # Cerrar la conexión en el bloque finally
        conexion.close()

@excepcion_precio.route('/guardar', methods=['POST','GET'])
def guardarExcepcion():
    conexion=obtener_conexion()

    sku_indivisible = request.form['sku_indivisible']
    precio = request.form['precio']
    usuario = session['usuario']
    fecha_y_hora_actual = datetime.now()

    try:

        with conexion.cursor() as cursor:
            cursor.execute('SELECT * FROM productos WHERE sku_padre = %s',(sku_indivisible))
            data = cursor.fetchall()

        if(data):
            with conexion.cursor() as cursor:
                cursor.execute('SELECT id, sku_indivisible, precio, fecha, usuario FROM exepciones_precio WHERE sku_indivisible = %s',(sku_indivisible))
                data2 = cursor.fetchall()
            
            if(data2):
                flash("SKU INDIVISIBLE EXITE EN LA TABLA",'success')
                return redirect(url_for('excepcion_precio.excepcion')) 
            else:
                with conexion.cursor() as cursor:
                    cursor.execute('INSERT INTO exepciones_precio (sku_indivisible, precio, fecha, usuario) VALUES (%s,%s,%s,%s)', (sku_indivisible, precio, fecha_y_hora_actual, usuario))
                    conexion.commit()
        else:
            flash("SKU INDIVISIBLE NO EXITE",'success')
            return redirect(url_for('excepcion_precio.excepcion')) 
        
       
        flash("Excepción guardada correctamente",'success')
        return redirect(url_for('excepcion_precio.excepcion')) 
    #return redirect(url_for('excepcion_precio.excepcion'),data_precios = data_precios)  

    except Exception as e:
        # Manejar la excepción aquí, por ejemplo, imprimir un mensaje de error
        print("Ocurrió un error al ejecutar la consulta:", e)
        flash("Ocurrió un error al ejecutar la consulta:", e)
        return redirect(url_for('excepcion_precio.excepcion')) 
        # También puedes revertir la transacción si es necesario
        conexion.rollback()
    finally:
        # Cerrar la conexión en el bloque finally
        conexion.close()
    
#eliminar excepcion
@excepcion_precio.route('/deleteIemPrecio/<id>')
def deleteIemPrecio(id):
    conexion=obtener_conexion()

    try:

        with conexion.cursor() as cursor:
            cursor.execute('DELETE from exepciones_precio WHERE id = %s',(id))
            conexion.commit()
        
        flash("Precio eliminado correctamente",'success')
        return redirect(url_for('excepcion_precio.excepcion')) 

    except Exception as e:

         # Manejar la excepción aquí, por ejemplo, imprimir un mensaje de error
        print("Ocurrió un error al ejecutar la consulta:", e)
        flash("Ocurrió un error al ejecutar la consulta:", e)
        return redirect(url_for('excepcion_precio.excepcion')) 
        # También puedes revertir la transacción si es necesario
        conexion.rollback()

    finally:

        conexion.close()


@excepcion_precio.route('/validaPrecioMinimo')
def validaPrecioMinimo():

    try:
        conexion=obtener_conexion()
        with conexion.cursor() as cursor:
            cursor.execute('SELECT id, coste, pva, sku_indivisible FROM precios WHERE coste != 0')
            data_precios = cursor.fetchall()
            #print(data_precios)

            for x in data_precios:
                id = x[0]
                coste = x[1]
                precio_minimo = round(x[1] * 1.5,2)
                pva = x[2]
                sku_indivisible = x[3]

                #print(precio_minimo, pva)

                if(precio_minimo < pva):

                    print(id, precio_minimo,' - ',pva, ' - ', sku_indivisible)

                else:

                    print('ok', coste, ' - ' ,precio_minimo, ' - ', pva, ' - ', sku_indivisible)


        return 'hola'
    
    except Exception as e:

         # Manejar la excepción aquí, por ejemplo, imprimir un mensaje de error
        print("Ocurrió un error al ejecutar la consulta:", e)
        flash("Ocurrió un error al ejecutar la consulta:", e)
        return redirect(url_for('excepcion_precio.excepcion')) 
        # También puedes revertir la transacción si es necesario
        conexion.rollback()

    finally:

        conexion.close()

 
#calcula promocion
@excepcion_precio.route('/calculaPromocion')
def calculaPromocion():

    try:
        conexion=obtener_conexion()
        with conexion.cursor() as cursor:
            cursor.execute('SELECT id, sku_indivisible, precio, fecha, usuario FROM exepciones_precio')
            data_precios = cursor.fetchall()
            #print(data_precios)

            

            for x in data_precios:
                
                sku_indivisible_ex = x[1]
                precio_ex = x[2]

                print(precio_ex, 'precio tabla excepciones' , sku_indivisible_ex)

                with conexion.cursor() as cursor:
                    cursor.execute('SELECT id, sku_indivisible, pva FROM precios WHERE sku_indivisible = %s',(sku_indivisible_ex))
                    data_ex_precio = cursor.fetchall()

                    for j in data_ex_precio:

                        precio_pr = j[2]
                        print(precio_pr, 'precio tabla precios', sku_indivisible_ex)

                
        return('hola')
    except Exception as e:

         # Manejar la excepción aquí, por ejemplo, imprimir un mensaje de error
        print("Ocurrió un error al ejecutar la consulta:", e)
        flash("Ocurrió un error al ejecutar la consulta:", e)
        return redirect(url_for('excepcion_precio.excepcion')) 
        # También puedes revertir la transacción si es necesario
        conexion.rollback()

    finally:

        conexion.close()


#actualizar en precios las excepciones de la tabla excepciones precio
@excepcion_precio.route('/EjecutaExcepciones')
def ejecutaExcepciones():

    try:
        conexion=obtener_conexion()
        with conexion.cursor() as cursor:
            cursor.execute('SELECT sku_indivisible, precio FROM exepciones_precio')
            data_precios = cursor.fetchall()
            
            #print(data_precios)

            for x in data_precios:
                
                sku_excepciones = x[0]
                precio = x[1]

                with conexion.cursor() as cursor:
                    cursor.execute('SELECT sku_indivisible FROM precios WHERE sku_indivisible = %s',(sku_excepciones))
                    exepciones = cursor.fetchall()

                for j in exepciones:

                    sku_indivisible_e = j[0]

                    with conexion.cursor() as cursor:
                        cursor.execute('UPDATE precios SET pva = %s WHERE sku_indivisible = %s',(precio, sku_indivisible_e))
                        conexion.commit()
                
        return('hola')
    except Exception as e:

        # Manejar la excepción aquí, por ejemplo, imprimir un mensaje de error
        print("Ocurrió un error al ejecutar la consulta:", e)
        flash("Ocurrió un error al ejecutar la consulta:", e)
        return redirect(url_for('excepcion_precio.excepcion')) 
        # También puedes revertir la transacción si es necesario
        conexion.rollback()

    finally:

        conexion.close()








