from flask import Flask, render_template, url_for, request,jsonify, json ,make_response, redirect, Response, Blueprint,send_from_directory
from woocommerce import API
import application
from . import woo
from ast import dump
import stripe
import datetime
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
import requests
import mysql.connector
from mysql import connector
import pandas as pd
import csv
import sqlite3
import xlrd
import io
import xlwt
import openpyxl
from datetime import datetime
from datetime import date
import iop

@woo.route('/integracion')
def integra():
    
    return render_template('tienda.html')

@woo.route('/woocommerce')
def sincronizaInventario():

    wcapi = API(
        url = 'https://wondermarket.es',
        consumer_key='ck_b2977f45f71a91bc1a94a1c677fa1cac118a0fbe',
        consumer_secret='cs_a2da1896983bc351e5ff476a316e78407f1b6bef',
        wp_api=True,
        version='wc/v3',
        query_string_auth=True 
    )
    page = 1
    paila = 0
    for i in range(201):
        
        data_2 = wcapi.get("products", params={"per_page": 10,'page': page}).json()
        #print(data_2)
        page += 1
        for x in data_2:
            sku = x['sku']
            id = x['id']
            price = x['price']
            stock_quantity = x['stock_quantity']
            #print(sku, stock_quantity)
            conexion=obtener_conexion()
            with conexion.cursor() as cursor:
                cursor.execute("SELECT sku_indivisible, sku_padre, cantidad, tipo_producto FROM productos WHERE sku_padre =  %s", sku)
                result_set = cursor.fetchone()
                
                if(result_set):
                    #print(sku)
                    sku_indivisible = result_set[0]
                    print(sku_indivisible)
                    sku_padre = result_set[1]
                    relacion = int(result_set[2])
                    tipo_producto = result_set[3]
                    
                    if(relacion == 1):

                        conexion=obtener_conexion()
                        with conexion.cursor() as cursor:
                            cursor.execute("SELECT cantidad  FROM inventario WHERE sku_indivisible =  %s", sku_indivisible)
                            result_set_2 = cursor.fetchone()
                            qty_bd = int(result_set_2[0])
                            
                            if result_set_2 is not None and len(result_set_2) > 0:
                                qty_bd = int(result_set_2[0])
                                print("Quantity:", qty_bd)

                                data = {
                                "stock_quantity": qty_bd
                                }
                                wcapi.put('products/' + str(id), data).json()
                            else:
                                print("No results found or result_set_2 is None", sku, sku_indivisible)

                            #print(sku_indivisible, sku_padre, relacion , qty_bd)

                            

                        ##### actualiza can del inventario
                    elif(relacion > 1):
                        
                        conexion=obtener_conexion()
                        with conexion.cursor() as cursor:
                            cursor.execute("SELECT cantidad  FROM inventario WHERE sku_indivisible =  %s", sku_indivisible)
                            result_set_2 = cursor.fetchone()

                            if result_set_2 is not None and len(result_set_2) > 0:
                                qty_bd = int(result_set_2[0])
                                print("Quantity:", qty_bd)
                                qty_bd = int(result_set_2[0])

                                qty_final = qty_bd / relacion
                                
                                data = {
                                    "stock_quantity": int(qty_final)
                                }
                                wcapi.put('products/' + str(id), data).json()

                                #print(sku_indivisible, sku_padre,relacion , qty_bd , int(qty_final), id)

                                #print(sku_indivisible, sku_padre, relacion, tipo_producto)
                            else:
                                print("No results found or result_set_2 is None",sku, sku_indivisible)
                            
                               
                    else:
                        paila += 1
                        #print(paila)
                    #print(sku, stock_quantity)
    
    return render_template('tienda.html')

@woo.route('/orders')
def ordenes():

    db = 'inventario'
    table = 'estados_pedidos'
    path = "C:/python/cambio_estado.xlsm"
    
    url = "mysql+mysqlconnector://root:@localhost/"
    engine = create_engine(url +db)
    df = pd.read_excel(path)
    print("read ok")
    df.to_sql(name = table, con = engine, if_exists='append', index= False)
    
    conexion=obtener_conexion()
    with conexion.cursor() as cursor:
        cursor.execute("SELECT id_pedido, nuevo_estado  FROM estados_pedidos")
        pedidos = cursor.fetchall()
        print(pedidos)
        wcapi = API(
            url = 'https://wondermarket.es',
            consumer_key='ck_b2977f45f71a91bc1a94a1c677fa1cac118a0fbe',
            consumer_secret='cs_a2da1896983bc351e5ff476a316e78407f1b6bef',
            wp_api=True,
            version='wc/v3',
            query_string_auth=True 
        )

        for x in pedidos:
            print(x[0], x[1])

            id_pedido = str(x[0])
            nuevo_estado = x[1]

            data = {
                "status": nuevo_estado
            }

            print(wcapi.put("orders/"+id_pedido , data).json())

        cursor.execute("TRUNCATE TABLE estados_pedidos")
        conexion.commit()
        flash("Estados de pedido actualizados correctamente")
    
    return render_template('tienda.html')

@woo.route('/pedidos')
def pedidosWonder():

    wcapi = API(
            url='https://wondermarket.es',
            consumer_key='ck_b2977f45f71a91bc1a94a1c677fa1cac118a0fbe',
            consumer_secret='cs_a2da1896983bc351e5ff476a316e78407f1b6bef',
            wp_api=True,
            version='wc/v3',
            query_string_auth=True 
        )
    page = 1
    paila = 0
    order_statuses = ['processing', 'pending', 'on-hold']  # Estados de pedido que deseas incluir

     # Crear un nuevo libro de Excel y una hoja de trabajo
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.append(['Númerode pedido', 'Estado del pedido', 'traking', 'Fecha del pedido', 'Nombre (envío)', 'Nombre (Facturación)','Apellido (envío)', 'Apellido (Facturación)' ,'Empresa', 'Nota del cliente', 'Dirección envío', 'Dirección facturación', 'Ciudad (envío)', 'Ciudad (facturación)', 'Código de provincia (envío)', 'Código de provincia (facturación)', 'Código postal (envío)', 'Código postal (facturación)', 'Código del país (envío)', 'Código del país (facturación)', 'Correo electrónico', 'Teléfono', 'SKU', '# Articulo','Item Name', 'Cantidad', 'Coste de artículo', 'Código de cupón', 'Importe de descuento', 'Importe de impuestos del descuento', 'Título del método de pago', 'Importe de descuento del carrito', 'Importe del subtotal del pedido', 'Título del método de envío', 'Importe de envío del pedido', 'Importe reembolsado del pedido', 'Importe total del pedido', 'Importe total de impuestos del pedido'])


    while True:
        datos_pedidos = wcapi.get("orders", params={"per_page": 30, 'page': page, 'status': ','.join(order_statuses)}).json()

        if not datos_pedidos:  # Si no hay más pedidos disponibles, salir del bucle
            break

        for order in datos_pedidos:
            order_id = order['id']
            order_status = order['status']
            order_date = order['date_created']
            
            num_producto = 0

            #codigo cupon y importe descuento, importe de impuestos del descuento
            coupon_code = ''
            discount_amount = 0
            discount_tax = 0
            #importe descuento carrito
            cart_discount = order['discount_total'] if 'discount_total' in order else 0
            #if 'coupon_lines' in order:
                #coupon_code = order['coupon_lines'][0]['code']
                #discount_amount = order['coupon_lines'][0]['discount']
                #discount_tax = order['coupon_lines'][0]['discount_tax']

            # Obtener el método de envío y el coste del envio
            shipping_method = ''
            if 'shipping_lines' in order:
                shipping_method = order['shipping_lines'][0]['method_title']
                shipping_cost = order['shipping_lines'][0]['total']

            # Obtener el importe reembolsado
            refunded_amount = order['total_refunded'] if 'total_refunded' in order else 0

            # Obtener el importe total del pedido
            total_amount = order['total']
           

            # Obtener el importe total de impuestos del pedido
            total_tax = order['total_tax'] if 'total_tax' in order else 0

            # Obtener el número de seguimiento
            tracking_number = ''
            if 'tracking_numbers' in order and len(order['tracking_numbers']) > 0:
                tracking_number = order['tracking_numbers'][0]

            for item in order['line_items']:
                
                customer_name_facturacion = order['billing']['first_name'] + ' ' + order['billing']['last_name']
                customer_name_envio = order['shipping']['first_name'] + ' ' + order['shipping']['last_name']
                nombre_envio = order['shipping']['first_name']
                nombre_facturacion = order['billing']['first_name']
                apellidos_envio = order['billing']['last_name']
                apellidos_facturacion = order['shipping']['last_name']
                empresa = order['billing']['company']
                direccion_facturacion = order['shipping']['address_1'] + ' ' + order['shipping']['address_2']
                direccion_envio = order['billing']['address_1'] + ' ' +order['billing']['address_2']
                ciudad_facturacion = order['billing']['city']
                ciudad_envio = order['shipping']['city']
                codigo_provincia_envio = order['shipping']['state']
                codigo_provincia_facturacion = order['billing']['state']
                codigo_postal_envio = order['shipping']['postcode']
                codigo_postal_facturacion = order['billing']['postcode']
                codigo_pais_envio = order['shipping']['country']
                codigo_pais_facturacion = order['billing']['country']
                correo_electronico = order['billing']['email']
                telefono = order['billing']['phone']
                sku = item['sku']
                quantity_sold = item['quantity']
                product_name = item['name']
                price = item['price']
                titulo_metodo_pago = order['payment_method_title']
                subtotal = order['subtotal'] if 'subtotal' in order else 0
                
                nota_cliente = order['customer_note']
                num_producto += 1

                # Insertar en la base de datos
                conexion = obtener_conexion()
                with conexion.cursor() as cursor:
                    cursor.execute("INSERT INTO pedidos (order_id, status, cod_seguimiento,fecha_pedido ,nombre_envio, nombre_facturacion,apellido_envio, apellido_facturacion ,empresa, nota_cliente, direccion_facturacion, direccion_envio, ciudad_envio, ciudad_facturacion, cod_provincia_envio, cod_provincia_facturacion, cod_postal_envio, cod_postal_facturacion,cod_pais_envio, cod_pais_facturacion,  email, phone, sku, no_articulo ,nombre_producto, cantidad_vendida, precio, cod_cupon,importe_descuento,  importe_impuestos_descuento, metodo_pago, importe_descuento_carrito,importe_subtotal, metodo_envio,  importe_envio_pedido, importe_reembolso, importe_total, importe_total_impuestos) VALUES (%s, %s, %s, %s, %s,%s, %s, %s, %s, %s,%s, %s, %s, %s, %s,%s,%s, %s, %s, %s, %s,%s, %s, %s, %s, %s,%s, %s, %s, %s, %s,%s, %s, %s, %s, %s,%s,%s)",
                                   (order_id, order_status, tracking_number,order_date,nombre_envio, nombre_facturacion,apellidos_envio,apellidos_facturacion, empresa, nota_cliente, direccion_facturacion, direccion_envio, ciudad_envio,ciudad_facturacion, codigo_provincia_envio, codigo_provincia_facturacion, codigo_postal_envio, codigo_postal_facturacion, codigo_pais_envio, codigo_pais_facturacion, correo_electronico, telefono, sku, num_producto  ,product_name, quantity_sold, price, coupon_code, discount_amount, discount_tax, titulo_metodo_pago, discount_tax, subtotal, shipping_method,shipping_cost , refunded_amount, total_amount, total_tax))
                    conexion.commit()
                
                 # Insertar en la hoja de trabajo
                sheet.append([order_id, order_status, tracking_number,order_date,nombre_envio, nombre_facturacion, apellidos_envio,apellidos_facturacion,empresa, nota_cliente, direccion_facturacion, direccion_envio, ciudad_envio,ciudad_facturacion, codigo_provincia_envio, codigo_provincia_facturacion, codigo_postal_envio, codigo_postal_facturacion, codigo_pais_envio, codigo_pais_facturacion, correo_electronico, telefono, sku, num_producto  ,product_name, quantity_sold, price, coupon_code, discount_amount, discount_tax, titulo_metodo_pago, discount_tax, subtotal, shipping_method,shipping_cost , refunded_amount, total_amount, total_tax])
                

        page += 1

    # Obtener la fecha y hora actual
    fecha_y_hora_actual = datetime.now()

    # Formatear la fecha y hora actual como una cadena (por ejemplo, YYYY-MM-DD_HH-MM-SS)
    formato_fecha_hora = fecha_y_hora_actual.strftime("%Y-%m-%d_%H-%M-%S")

    # Concatenar la fecha y hora formateada al nombre del archivo
    nombre_archivo = 'C:\\python\\pedidos_wonder\\pedidos_wonder_' + formato_fecha_hora + '.xlsx'

    # Guardar el libro de Excel
    workbook.save(nombre_archivo)

    flash('Todos los pedidos en estado "procesando" y "pendiente" han sido obtenidos y desglosados por producto en C:\python\pedidos_wonder\ ')
    return render_template('tienda.html')



@woo.route('/venta', methods = ['GET', 'POST'])
def venta():

    print('se hizo una venta')



    return 'venta'

@woo.route('/webhookWoocomerce', methods=['POST', 'GET'])
def webhookwoocomerce():
    if request.method == 'POST':
        payload = request.get_data(as_text=True)
        sig_header = request.headers.get('Stripe-Signature')

        endpoint_secret = 'sk_test_noUer6t5paCoZuvTsiNyKzEQ00GngtWEy6'  # Obtén esto desde tu panel de Stripe

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
        except ValueError as e:
            # Invalid payload
            return jsonify(success=False, message="Invalid payload"), 400
        except stripe.error.SignatureVerificationError as e:
            # Invalid signature
            return jsonify(success=False, message="Invalid signature"), 400

        # Handle the event
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            # Aquí puedes procesar los datos de la venta
            print('Checkout Session ID:', session['id'])
            print('Customer Email:', session['customer_email'])
            print('Amount Total:', session['amount_total'])
            print('Payment Status:', session['payment_status'])
            # Agrega aquí la lógica para procesar la venta

            # Puedes devolver los datos o realizar alguna otra acción

        return jsonify(success=True), 200
    elif request.method == 'GET':
        print('hola desde webhook venta')
        return 'hola', 200


@woo.route('/webhook', methods=['POST', 'GET'])
def webhook():
    url = 'https://api.miravia.com/v2/product/get'  # URL correcta de la API de Miravia
    appkey = '507264'
    appSecret = 'PDVcqLbxuJriMkxltJdHUAGO9M3kgejl'
    access_token = '50000101238q2nQzgvDkPARRfWeiq7su2ekiyh3FTtojwntRAL10ec1e2c0QJunw'  # Token de acceso válido

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    params = {
        'product_id': '1357296984086901',
        'seller_skus': '["TESTING_PRODUCT_DECEMBER_467d4d03-4efc-4d78-9569-78971ab02c18"]',
        'max_created_at': '1704884033000',
        'page_size': '10',
        'page': '1',
        'extraInfo_filter': '["quality_control_log"]',
        'status': 'ALL'
    }

    response = requests.get(url, headers=headers, params=params)
    response_data = response.json()

    print(response_data)
    return response_data
    

@woo.route('/claseEnvio')
def claseEnvio():
    # Configura la conexión a la API
    wcapi = API(
        url='https://wondermarket.es',
        consumer_key='ck_b2977f45f71a91bc1a94a1c677fa1cac118a0fbe',
        consumer_secret='cs_a2da1896983bc351e5ff476a316e78407f1b6bef',
        wp_api=True,
        version='wc/v3',
        query_string_auth=True
    )

    # Obtener todas las clases de envío y mapear sus IDs a sus nombres
    shipping_classes_response = wcapi.get("products/shipping_classes")
    shipping_classes = shipping_classes_response.json()
    shipping_classes_dict = {cls['id']: cls['name'] for cls in shipping_classes}

    # Obtener la clase de envío 'DEFAULT'
    default_class_id = None
    for cls in shipping_classes:
        if cls['name'] == 'DEFAULT':
            default_class_id = cls['id']
            break

    if default_class_id is None:
        return "Clase de envío 'DEFAULT' no encontrada.", 400

    # Función para obtener todos los productos con paginación
    def obtener_todos_los_productos(wcapi, per_page=100):
        productos = []
        pagina = 1
        while True:
            response = wcapi.get("products", params={"per_page": per_page, "page": pagina})
            data = response.json()
            if not data:
                break
            productos.extend(data)
            pagina += 1
        return productos

    # Obtener todos los productos
    productos = obtener_todos_los_productos(wcapi)

    # Crear una cadena para almacenar los resultados
    resultados = []

    for product in productos:
        product_name = product['name']
        shipping_class_id = product.get('shipping_class_id')
        shipping_class_name = shipping_classes_dict.get(shipping_class_id, 'No asignada')

        if shipping_class_name in ['No asignada', 'Plantilla de Amazon-copia', 'Plantilla de Amazon', 'Frescos y Congelados']:
            
            print(product_name, shipping_class_name )
            # Actualizar la clase de envío del producto a 'DEFAULT'
            #update_response = wcapi.put(f"products/{product['id']}", {"shipping_class_id": default_class_id})
            #if update_response.status_code == 200:
                #resultado = f"Producto: {product_name} (ID: {product['id']}) actualizado a la clase de envío DEFAULT.\n"
        else:
            #resultado = f"Error al actualizar el producto: {product_name} (ID: {product['id']}). Detalle del error: {update_response.json()}\n"
        #print(resultado)
            print('hello')

    # Unir todos los resultados en una sola cadena
    resultados_str = '\n'.join(resultados)
    
    return resultados_str