import cv2
import threading
import time
import sys
import os

# 0. El fix de Windows (Igual que en tu script simple)
if sys.platform.startswith('win'):
    os.environ["OPENCV_VIDEOIO_MSMF_ENABLE_HW_TRANSFORMS"] = "0"

class WebcamThreaded:
    def __init__(self, src=0, width=1920, height=1080):
        self.src = src
        self.width = width
        self.height = height
        
        self.grabbed = False
        self.frame = None
        self.started = False
        self.read_lock = threading.Lock()
        
        # --- INICIALIZACIÓN IDÉNTICA A TU SCRIPT QUE FUNCIONA ---
        print("⚡ Inicializando cámara con configuración DSHOW...")
        self.cap = cv2.VideoCapture(self.src, cv2.CAP_DSHOW)
        
        # Definimos el codec una sola vez en variable para reusarlo
        mj_fourcc = cv2.VideoWriter_fourcc('M', 'J', 'P', 'G')

        # 1. Codec PRIMERA VEZ
        self.cap.set(cv2.CAP_PROP_FOURCC, mj_fourcc)
        
        # 2. Resolución
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        
        # 3. FPS
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        
        # 4. Exposición y Brillo
        self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1) # Manual
        self.cap.set(cv2.CAP_PROP_BRIGHTNESS, 128)
        
        # 5. Codec SEGUNDA VEZ (Como pediste, "lo del codec al final")
        # Esto a veces fuerza al driver a reinicializar el pipeline con los nuevos settings
        self.cap.set(cv2.CAP_PROP_FOURCC, mj_fourcc)

        # 6. IMPORTANTE PARA HILOS: BufferSize = 1
        # Esto evita que se acumulen frames viejos y genere delay ("lag")
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        # Lectura inicial para asegurar que arrancó
        self.grabbed, self.frame = self.cap.read()
        if not self.grabbed:
            print("❌ Advertencia: No se pudo capturar el primer frame.")

    def start(self):
        if self.started:
            return self
        self.started = True
        self.thread = threading.Thread(target=self.update, args=(), daemon=True)
        self.thread.start()
        print("✅ Hilo de captura iniciado.")
        return self

    def update(self):
        """Bucle infinito que corre en paralelo"""
        while self.started:
            grabbed, frame = self.cap.read()
            
            with self.read_lock:
                self.grabbed = grabbed
                if grabbed:
                    self.frame = frame
            
            # NOTA: No ponemos time.sleep() aquí porque cap.read() ya espera
            # al hardware (33ms aprox para 30fps). Poner sleep agrega lag.
            if not grabbed:
                time.sleep(0.1) # Solo dormimos si falla la cámara para no quemar CPU

    def read(self):
        """Devuelve el frame más reciente"""
        with self.read_lock:
            if self.frame is None:
                return None
            # Hacemos copy() porque estamos en hilos y no queremos "tearing"
            # (que la imagen cambie mientras la dibujas)
            return self.frame.copy()

    def stop(self):
        self.started = False
        if hasattr(self, 'thread'):
            self.thread.join()
        self.cap.release()

# --- PRUEBA CON HILOS ---
if __name__ == "__main__":
    # Instanciar e iniciar
    cam = WebcamThreaded(src=0, width=1920, height=1080).start()
    
    # Darle 1 segundo al hardware para acomodarse
    time.sleep(1)

    print("🎥 Iniciando visualización...")
    
    # Variables FPS
    prev_time = time.time()
    frame_count = 0
    fps_display = 0

    while True:
        # Esto es instantáneo gracias al hilo
        frame = cam.read()
        
        if frame is not None:
            # Tu lógica de FPS
            frame_count += 1
            curr_time = time.time()
            elapsed = curr_time - prev_time
            
            if elapsed >= 1:
                fps_display = frame_count / elapsed
                prev_time = curr_time
                frame_count = 0
            
            # Dibujar
            cv2.putText(frame, f"FPS: {fps_display:.2f}", (10, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            cv2.imshow("Webcam Threaded V3", frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cam.stop()
    cv2.destroyAllWindows()
