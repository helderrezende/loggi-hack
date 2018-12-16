import pandas as pd
import re
import unidecode
import glob
import os
from sklearn import preprocessing
import geopy.distance
import datalayer

def fill_na_by_mean(data, columns):
    for column in columns:
        data[column] = data.groupby(['uf'])[column].apply(lambda x: x.fillna(x.mean()))
        
    return data

def set_scale_columns(data, columns):
    for column in columns:
        data['scaled_' + column] = preprocessing.minmax_scale(data[column])
        
    return data

def drop_scaled_columns(data, columns):
    for column in columns:
        data = data.drop(['scaled_' + column], 1)
        
    return data

def calculate_distance_airport(table):
    table['distance_airport'] = table.apply(lambda x: geopy.distance.geodesic((x['latitude_airport'], x['longitude_airport']), (x['latitude'], x['longitude'])).km, 1)
    table.loc[table['tem_malha'] == 1, 'distance_airport'] = 0
    
    return table
    
def calculate_score(table):
    ### CRITERIO
    ## viabilidade_terrestre - 15
    ## viabilidade_aerea - 20
    ## custo_indireto - 10
    ## custo_direto - 20
    ## lucro - 35
    
    # viabilidade_terrestre = caminhao, caminhonete, camioneta, motocicleta
    # viabilidade_aerea = quantidade_decolagens
    # custo_indireto = indice_roubo, preco_gasolina, preco_diesel_s10
    # custo_direto = distancia_cajamar, distance_airport
    # lucro = pib, area_urbana, idh_renda
    
    table['viabilidade_terrestre'] = (1*table['scaled_caminhao'] + 1*table['scaled_camioneta'] + 1*table['scaled_caminhonete'] + 1*table['scaled_motocicleta'])/4
    table['viabilidade_aerea'] = 1*table['scaled_quantidade_decolagens']
    table['custo_indireto'] = (1*table['scaled_indice_roubo'] + 1*table['scaled_preco_gasolina'] + 1*table['scaled_preco_diesel_s10'])/3
    table['custo_direto'] = (2*table['scaled_distancia_cajamar'] + 1* table['scaled_distance_airport'])/3
    table['lucro'] = (1*table['scaled_pib'] + 1*table['scaled_area_urbana'] + 1* table['idh_renda'])/3
    
    table['score'] = 0.15 * table['viabilidade_terrestre'] + 0.15 * table['viabilidade_aerea'] + 0.15 - table['custo_indireto'] + 0.20 - table['custo_direto'] + 0.35 * table['lucro']
    
    return table


def run():
    # loading tables
    airports = datalayer.get_airports()
    cities = datalayer.get_cities() 
    municipios = datalayer.get_municipios()
    frotas = datalayer.get_frotas()
    decolagens = datalayer.get_decolagens()
    gasolina, gasolina_uf = datalayer.get_gasolina()
    area_urbana = datalayer.get_area_urbana()
    pib_municipio = datalayer.get_pib_municipio()
    geo_municipios = datalayer.get_geo_municipios()
    sinistros = datalayer.get_sinistros()
    idh_renda = datalayer.get_idh_renda()

    airports_uf = datalayer.get_airport_with_uf(airports, municipios)
    airports_uf = airports_uf.rename(columns={'UF':'uf'})
    airports_uf = airports_uf.merge(decolagens, on='codigo', how='left')
    airports_uf = airports_uf.sort_values('quantidade_decolagens', ascending=False)
    airports_uf_decolagens = airports_uf.groupby('uf', as_index=False)['quantidade_decolagens'].first()
    airports_distance = airports_uf_decolagens.merge(airports_uf[['uf', 'quantidade_decolagens', 'latitude_airport', 'longitude_airport']], on=['uf', 'quantidade_decolagens'])
    
    cities = cities.merge(geo_municipios, on=['city', 'uf'])
    cities = cities.merge(idh_renda, on=['city', 'uf'])
    cities = cities.merge(sinistros, on='uf')
    cities = cities.merge(airports_distance, on='uf')
    cities = cities.merge(frotas, on=['city', 'uf'], how='left')
    cities = cities.merge(gasolina, on=['city', 'uf'], how='left')
    cities = cities.merge(area_urbana, on=['city', 'uf'], how='left')
    cities = cities.merge(pib_municipio, on=['city', 'uf'], how='left')
    cities['preco_gasolina'] = cities['preco_gasolina'].where(cities['preco_gasolina'].notnull(), cities['uf'].map(gasolina_uf.set_index('uf')['preco_gasolina'])).fillna(cities['preco_gasolina'].mean())
    cities['preco_diesel_s10'] = cities['preco_diesel_s10'].where(cities['preco_diesel_s10'].notnull(), cities['uf'].map(gasolina_uf.set_index('uf')['preco_diesel_s10'])).fillna(cities['preco_diesel_s10'].mean())
    cities = cities[cities['atendido_loggi'] == 'não']   
    
    
    cities = calculate_distance_airport(cities)
    #result = cities.merge(airports_uf, on=['city', 'uf'], how='left')
    
    columns = ['caminhao', 'camioneta', 'caminhonete', 'motocicleta', 'area_urbana', 'pib']
    cities = fill_na_by_mean(cities, columns)
    
    columns = ['caminhao', 'camioneta', 'caminhonete', 'motocicleta', 'area_urbana',
               'pib', 'quantidade_decolagens', 'indice_roubo', 'preco_gasolina', 
               'preco_diesel_s10', 'distancia_cajamar', 'distance_airport', 'idh_renda']
    
    cities = set_scale_columns(cities, columns)
    cities = calculate_score(cities)
    cities = drop_scaled_columns(cities, columns)
    cities = cities.sort_values('score', ascending=False)
    
    ## saving final result
    cities.to_csv('data/output/cidades.csv')
    
    return cities


if __name__ == "__main__":
    cities = run()