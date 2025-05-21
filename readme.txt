api server 0.0.0.0
username freqtrader
password fraqtrader


Parfait Ibrahim 👌 ! Puisque ton chemin Windows est bien :

> `C:\ft_userdata`

Je vais te donner **toutes les commandes Docker Freqtrade adaptées à ton chemin Windows**, de manière **claire, complète et classée** pour que tu puisses tout gérer facilement 💪.

---

## ✅ **PRÉREQUIS** (à faire une fois si nécessaire)

Crée le répertoire `user_data` et vérifie qu’il contient bien ton fichier `config.json` et ta stratégie :

```plaintext
C:\ft_userdata\
  ├── config.json
  ├── user_data/
      ├── strategies/
          └── HybridAdvancedStrategy.py
      ├── tradesv3.sqlite
      └── ...
```

---

## 🧯 1. **ARRÊTER LES CONTENEURS ACTUELS**

Tu peux arrêter les conteneurs avec leurs noms exacts (remplacés ici avec les tiens) :

```powershell
docker stop ft_userdata-freqtrade-run-60d2ea1e435f
docker stop freqtrade
```

> 🔁 Refais cette commande à chaque fois que tu veux arrêter le bot ou le dashboard.

---

## 🚀 2. **LANCER LE BOT EN MODE TRADING**

```powershell
docker run -d ^
  --rm ^
  --name freqtrade-trading ^
  -v C:\ft_userdata:/freqtrade/user_data ^
  freqtradeorg/freqtrade:stable ^
  trade --config user_data/config.json
```

> 🟡 Cette commande lance le bot avec la config située dans `C:\ft_userdata`.

---

## 📊 3. **FAIRE UN BACKTEST**

```powershell
docker run --rm ^
  -v C:\ft_userdata:/freqtrade/user_data ^
  freqtradeorg/freqtrade:stable ^
  backtesting --config user_data/config.json --strategy HybridAdvancedStrategy
```

---

## 🧪 4. **AFFICHER LES RÉSULTATS DU BACKTEST (graphiques)**

```powershell
docker run --rm ^
  -v C:\ft_userdata:/freqtrade/user_data ^
  freqtradeorg/freqtrade:stable ^
  plot-dataframe --config user_data/config.json
```

---

## 🌐 5. **LANCER L’INTERFACE WEB (DASHBOARD)**

```powershell
docker run -d ^
  --name freqtrade ^
  -p 8080:8080 ^
  -v C:\ft_userdata:/freqtrade/user_data ^
  freqtradeorg/freqtrade:stable ^
  webserver --config user_data/config.json
```

> Ensuite, ouvre : [http://localhost:8080](http://localhost:8080)

---

## 🔍 6. **LISTER LES PAIRES DISPONIBLES (ex. Binance Futures)**

```powershell
docker run --rm ^
  -v C:\ft_userdata:/freqtrade/user_data ^
  freqtradeorg/freqtrade:stable ^
  list-pairs --config user_data/config.json
```

---

## 🧠 7. **COMMANDES UTILES**

### ➤ Voir les logs du bot (en temps réel) :

```powershell
docker logs -f freqtrade-trading
```

### ➤ Supprimer un conteneur (forcer l'arrêt et suppression) :

```powershell
docker rm -f freqtrade-trading
```

---

## 🛠️ 8. **EXEMPLE DE SCRIPT .BAT (AUTOMATIQUE)**

Tu peux créer un fichier `start_bot.bat` dans `C:\ft_userdata` contenant :

```bat
@echo off
echo === Démarrage du bot Freqtrade ===
docker stop freqtrade-trading
docker rm freqtrade-trading
docker run -d ^
  --rm ^
  --name freqtrade-trading ^
  -v C:\ft_userdata:/freqtrade/user_data ^
  freqtradeorg/freqtrade:stable ^
  trade --config user_data/config.json
pause
```

Et un autre script pour le dashboard : `start_dashboard.bat`

```bat
@echo off
echo === Lancement du Dashboard Freqtrade ===
docker stop freqtrade
docker rm freqtrade
docker run -d ^
  --name freqtrade ^
  -p 8080:8080 ^
  -v C:\ft_userdata:/freqtrade/user_data ^
  freqtradeorg/freqtrade:stable ^
  webserver --config user_data/config.json
pause
```

---

Souhaites-tu que je t’aide à créer ou vérifier ton `config.json`, ou ta stratégie `HybridAdvancedStrategy.py` pour éviter les erreurs comme *"No pair in whitelist"* ?
