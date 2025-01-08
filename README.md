# **OW DS Project**

This project builds upon the [WatchStats repository](https://github.com/krpouncy/WatchStats) to track and analyze Overwatch (OW) games. It extends the original functionality by introducing new models and components tailored specifically for OW2.

---

## **How to Install**

### **Step 1: Clone the WatchStats Repository**
1. Clone the [WatchStats repository](https://github.com/krpouncy/WatchStats) to your local machine:
   ```bash
   git clone https://github.com/krpouncy/WatchStats.git
   cd WatchStats
   ```

2. Install the required dependencies for the **WatchStats** repository:
   ```bash
   pip install -r requirements.txt
   ```

---

### **Step 2: Download Components from OW DS Project**
1. Download the OW2-specific components (`OW2_components` and `OW2_new` model folder) from this repository.

2. Copy the following:
   - `OW2_components` folder → Place into the `\user_components` folder in the WatchStats repository.
   - `OW2_new` folder → Place into the `\models` folder in the WatchStats repository.

---

### **Step 3: Clean Up Placeholder Components**
Remove placeholder/demo components from the WatchStats repository to avoid conflicts:

- **Delete the following folders:**
  - `\user_components\demo_components`
  - `\models\base_model`

---

### **Step 4: Install Additional Requirements**
Note about Dependencies:
Most of the dependencies listed in this project's requirements.txt are already included in the WatchStats repository's requirements.txt. If you have already installed the requirements for WatchStats, you may only need to install a few additional dependencies.

Install the required dependencies for the OW DS Project:
```bash
pip install -r requirements.txt
```

**Content of `requirements.txt`:**
```
eventlet==0.38.2
Flask==3.1.0
Flask_SocketIO==5.4.1
joblib
numpy
pandas==2.2.3
Pillow==11.1.0
pytesseract==0.3.13
pytest==8.3.4
scikit_learn==1.6.0
torch==2.5.1
torchvision==0.20.1
tqdm==4.67.1
```

---

### **Step 5: Run the Application**
1. Navigate to the `WatchStats` project directory:
   ```bash
   cd /path/to/WatchStats
   ```

2. Run the application:
   ```bash
   python main.py
   ```

3. Open the application in your browser:
   ```bash
   http://localhost:5000/
   ```

4. Follow the UI to track, analyze, and manage your OW2 game statistics.

---

## **Related Project**
Visit the [WatchStats repository](https://github.com/krpouncy/WatchStats) for the base implementation and additional details about how this project builds upon it.
