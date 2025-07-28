# 📊 Template Google Sheet

## Struttura Consigliata

Crea un Google Sheet con questa struttura esatta:

| A (Asset) | B (Quantità) | C (Prezzo Medio) | D (Prezzo Attuale) | E (Valore Attuale) | F (Investito Totale) | G (PnL %) | H (PnL €) | I (Ultimo Aggiornamento) |
|-----------|--------------|------------------|-------------------|-------------------|---------------------|-----------|-----------|-------------------------|
| BTC       | 0.5          | 45000            | 48000             | 24000             | 22500               | 6.67%     | 1500      | 2024-01-15 10:00:00     |
| ETH       | 2.0          | 2800             | 3000              | 6000              | 5600                | 7.14%     | 400       | 2024-01-15 10:00:00     |
| ADA       | 1000         | 0.45             | 0.50              | 500               | 450                 | 11.11%    | 50        | 2024-01-15 10:00:00     |
|           |              |                  |                   |                   |                     |           |           |                         |
| TOTALE    |              |                  |                   | 30500             | 28550               | 6.83%     | 1950      | 2024-01-15 10:00:00     |

## Formattazione Consigliata

### Intestazioni (Riga 1)
- **Font**: Arial, 12pt, Bold
- **Colore di sfondo**: Grigio chiaro (#f3f3f3)
- **Allineamento**: Centrato

### Dati (Righe 2+)
- **Font**: Arial, 11pt
- **Allineamento**: 
  - Colonna A (Asset): Sinistra
  - Colonne B-H: Destra
  - Colonna I (Timestamp): Centrato

### Formattazione Numerica
- **Colonna B (Quantità)**: 8 decimali
- **Colonne C, D, E, F (Prezzi e Valori)**: 2 decimali, formato valuta €
- **Colonna G (PnL %)**: 2 decimali, formato percentuale
- **Colonna H (PnL €)**: 2 decimali, formato valuta €

### Formattazione Condizionale
- **Colonna G (PnL %)**: 
  - Verde se > 0
  - Rosso se < 0
  - Grigio se = 0
- **Colonna H (PnL €)**:
  - Verde se > 0
  - Rosso se < 0
  - Grigio se = 0

## Configurazione Avanzata

### Filtri
Aggiungi filtri alla riga 1 per permettere il filtraggio e l'ordinamento dei dati.

### Grafici Consigliati
1. **Pie Chart**: Distribuzione del portafoglio per asset
2. **Line Chart**: Andamento del valore totale nel tempo
3. **Bar Chart**: PnL per asset

### Formule Utili
Puoi aggiungere formule per calcoli aggiuntivi:

```
// Valore totale portafoglio
=SUM(E2:E1000)

// PnL totale
=SUM(H2:H1000)

// Numero di asset
=COUNTA(A2:A1000)

// Asset con PnL positivo
=COUNTIF(G2:G1000, ">0")
```

## Note Importanti

1. **Nome del foglio**: Deve essere esattamente "Portfolio"
2. **Condivisione**: Condividi con l'email del service account
3. **Permessi**: Il service account deve avere permessi di "Editor"
4. **ID del foglio**: Copia dall'URL (parte tra /d/ e /edit)

## Esempio URL
```
https://docs.google.com/spreadsheets/d/1qz8T1p1ji1FuuGIWtfnbTNf3rB8gT7_j1u0u88EgW-M/edit#gid=0
```
L'ID del foglio è: `1qz8T1p1ji1FuuGIWtfnbTNf3rB8gT7_j1u0u88EgW-M` 