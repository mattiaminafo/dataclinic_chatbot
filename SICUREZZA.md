# 🔒 Note di Sicurezza

## ✅ Audit di Sicurezza Completato

Questo progetto è stato verificato per essere sicuro per repository pubblici.

### Protezioni Attive

- ✅ **Nessuna credenziale hardcoded** nel codice sorgente
- ✅ **File `.env.local`** nel `.gitignore` (non verrà mai committato)
- ✅ **File `.env`** nel `.gitignore`
- ✅ **Nessuna chiave API** esposta nel codice
- ✅ **Placeholder** nella documentazione invece di valori reali

### Variabili d'Ambiente

Tutte le credenziali devono essere configurate tramite variabili d'ambiente:

**Obbligatorie:**
- `OPENAI_API_KEY` - La tua API key OpenAI
- `ASSISTANT_ID` - ID dell'Assistant OpenAI
- `QDRANT_URL` - URL del cluster Qdrant
- `QDRANT_API_KEY` - API key di Qdrant

**Opzionali:**
- `QDRANT_COLLECTION_NAME` - Nome collection (default: `dataclinic_docs`)

### ⚠️ IMPORTANTE

1. **Mai committare** file `.env` o `.env.local`
2. **Mai hardcodare** credenziali nel codice
3. **Usa sempre** variabili d'ambiente per le credenziali
4. **Su Railway**, configura le variabili nel dashboard (non nel codice)

### Verifica Pre-Commit

Prima di ogni commit, verifica:

```bash
# Verifica che .env.local non sia tracciato
git status | grep .env.local

# Verifica che non ci siano chiavi hardcoded
grep -r "sk-proj-\|asst_\|eyJhbGci" --include="*.py" .
```

Se trovi qualcosa, NON committare!

---

**Ultimo audit:** Gennaio 2026
**Stato:** ✅ SICURO per repository pubblico

