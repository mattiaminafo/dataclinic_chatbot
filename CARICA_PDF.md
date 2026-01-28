# 📄 Come Caricare un PDF - Guida Pratica

## 🎯 Metodo Semplice

### Opzione A: PDF nella stessa cartella del progetto

1. **Copia il PDF** nella cartella `Chatbot_dataclinic`
2. **Apri il terminale** in quella cartella
3. **Esegui:**
   ```bash
   python upload_pdf.py nome_tuo_file.pdf
   ```

### Opzione B: PDF in un'altra cartella

Usa il percorso completo:

```bash
python upload_pdf.py /percorso/completo/al/file.pdf
```

**Esempi:**
```bash
# PDF sul Desktop
python upload_pdf.py ~/Desktop/dataclinic.pdf

# PDF in Downloads
python upload_pdf.py ~/Downloads/info.pdf

# PDF in una cartella specifica
python upload_pdf.py /Users/mattiaminafo/Documents/dataclinic.pdf
```

## 📋 Esempio Completo

```bash
# 1. Vai nella cartella del progetto
cd /Users/mattiaminafo/Desktop/Chatbot_dataclinic

# 2. Carica il PDF (sostituisci con il nome del tuo file)
python upload_pdf.py dataclinic.pdf

# Vedrai output tipo:
# Processando: dataclinic.pdf
# Estratte 10 pagine
# Testo diviso in 25 chunk
# Generando embeddings...
# Caricati 25 punti su Qdrant con successo
# ✅ dataclinic.pdf processato e caricato con successo!
```

## 🔍 Verifica che Funzioni

Dopo aver caricato, puoi testare il chatbot. Quando fai una domanda che riguarda il contenuto del PDF, il chatbot dovrebbe rispondere usando quelle informazioni!

## ⚠️ Problemi Comuni

**Errore: "File non trovato"**
- Verifica che il percorso sia corretto
- Usa `ls` per vedere i file nella directory

**Errore: "OPENAI_API_KEY non trovata"**
- Assicurati di avere un file `.env.local` con la tua API key

**Errore: "qdrant-client non installato"**
- Esegui: `pip install -r requirements.txt`

