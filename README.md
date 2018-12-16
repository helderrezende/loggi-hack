# loggi-hack
Projeto do Hackathon da Loggi realizado no dia 16/12/2018.

## Objetivo

O objetivo foi procurar e tratar a maior quantidade de dados para melhorar o modelo de escolha de municipio para a Loggi atuar.


## Dados


| tabela| funcao | fator | fonte |
| :---         |     :---:      |          ---: |          ---: |
| frotas   | get_frotas    | viabilidade_terrestre    | DENATRAN    | 
| decolagens     | get_decolagens  | viabilidade_aerea      |  ANAC    | 
| indice_roubo     | get_sinistros  | custo_indireto     |  SUSEP    | 
| preco_combustivel   | get_gasolina  | custo_indireto     |  ANP    | 
| distancia_cajamar   | get_cities  | custo_direto     |  LOGGI    | 
| pib   | get_pib_municipio  | lucro     |  IBGE    | 
| area_urbana   | get_area_urbana  | lucro     |  EMBRAPA    |
| idh_renda   | get_idh_renda  | lucro     |  ATLASBRASIL    | 

## Score

Foi utilizado o método parecido com priorização de projetos. São os 5 fatores:

* viabilidade_terrestre
* viabilidade_aerea 
* custo_indireto 
* custo_direto
* lucro

A modelagem é feita por pesos:

| fator| peso | 
| :---         |     :---:      | 
| viabilidade_terrestre   | 15%    | 
| viabilidade_aerea     | 15%  | 
| custo_indireto     | 15%  | 
| custo_direto   | 20%  | 
| lucro   | 35%  |



## Rodando o modelo

```
python score_calculator.py
```

Após rodar o python, o output será salvo em data/output.
