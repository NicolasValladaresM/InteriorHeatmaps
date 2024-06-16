import pandas
from PyQt5.QtWidgets import QDialog, QApplication
from PyQt5.uic import loadUi
from PyQt5.QtGui import QPixmap, QImage, QPainter, QFont
from PyQt5.QtCore import Qt,QRect,QDir, QPoint,QSize
from PyQt5.QtWidgets import *
from PyQt5 import QtGui
from pdf2image import convert_from_path
from PIL import Image
import sys
import os

#pdf, dwg, dwx
class ImageCropWindow(QDialog):
    
    def __init__(self, pixmap,label_img, parent=None): #Crear nueva ventana con atributo pixmap y label_img para pasar label de main
        super(ImageCropWindow, self).__init__(parent)
        self.setWindowTitle("Recorte de imagen")
        self.setGeometry(100, 100, 800, 800)
       # self.setFixedSize(800, 800) #colocar imagen en el centro
        self.selection_started = False
        self.selection_rect = QRect()
        self.image_path = pixmap
        self.pixmap = QPixmap(self.image_path)
        self.image_label = QLabel(self)
        self.image_label.setMaximumSize(label_img.size()) #ajustarse al label
        self.image_label.setScaledContents(True) #
        self.image_label.setPixmap(self.pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.image_label.setPixmap(self.pixmap)#
        self.Label_img = label_img


        self.origin = QPoint()
        self.rubberBand = QRubberBand(QRubberBand.Rectangle, self)
        

    def enviar_imagen(self):
        pixmap = self.image_label.pixmap()
        if pixmap is not None:
            self.label_img.setPixmap(pixmap)
        self.close()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self.image_label.pixmap())        
        painter.setRenderHint(QPainter.Antialiasing)
        
    def mousePressEvent(self, event):
        
        if event.button() == Qt.LeftButton:
            
            self.selection_rect.setTopLeft(event.pos())
            self.selection_rect.setBottomRight(event.pos())
            
            
            self.origin = QPoint(event.pos())
            self.rubberBand.setGeometry(QRect(self.origin, QSize()))
            self.rubberBand.show()
    

    def mouseMoveEvent(self, event):
            if not self.origin.isNull():
              self.rubberBand.setGeometry(QRect(self.origin, event.pos()).normalized())
              self.selection_rect.setBottomRight(event.pos())
              self.image_label.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.selection_started = False
           # obtener la escala de la imagen 
            scale_x = self.pixmap.width() / self.image_label.width()
            scale_y = self.pixmap.height() / self.image_label.height()
            
            #asignar a los ejes
            adjusted_rect = QRect(
                int(self.selection_rect.x() * scale_x),
                int(self.selection_rect.y() * scale_y),
                int(self.selection_rect.width() * scale_x),
                int(self.selection_rect.height() * scale_y)
            )

            cropped_image = self.pixmap.copy(adjusted_rect) #utilizar
            self.image_label.setPixmap(cropped_image.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

            file_path = os.path.join(QDir.currentPath(), "recortado.jpg")

            cropped_image.save(file_path)  # Guardar el archivo recortado
            pixmap = QPixmap(file_path) 
            self.Label_img.setPixmap(pixmap)
            self.image_label.update()

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        current_dir = os.path.dirname(os.path.abspath(__file__))

        ui_path = os.path.join(current_dir, "aplicacion.ui")

        loadUi(ui_path, self)  # cargar aplicación
        self.setWindowTitle("Heatmap")
        self.image_path = "" #localizacion del explorador donde se obtuvo la imagen y almacenar la ruta para cortar
        self.points = [] 
        self.crop_window = None  # guardar la instancia creada en clase crop_windows
        #conexiones con los botones del archivo .ui
        self.btn_subirimg.clicked.connect(self.cargarimg)
        self.btn_subirpdf.clicked.connect(self.cargarpdf)#
        
        self.btn_csv.clicked.connect(self.subircsv)
        self.Btn_save.clicked.connect(self.guardar)
        self.Btn_recortar.clicked.connect(self.recortar)
        self.selection_rect = QRect()
        
        self.imagen_cargada = False #controlar si se ha subido una imagen antes

    def cargarimg(self):
        file_dialog = QFileDialog()
        file_dialog.setNameFilters(["Images (*.png *.xpm *.jpg)", "All files (*)"]) #ver si es modificable
        file_dialog.selectNameFilter("Images (*.png *.xpm *.jpg)")
        #file_dialog.exec_()
        result = file_dialog.exec_()
        if result == QFileDialog.Accepted:
        # obtiene la ruta, seleccionando un archivo en la posición 0
            seleccionado = file_dialog.selectedFiles()
        #hacr algo cuando no se selecciona un archivo, para evitar que el programa crashee
            if seleccionado:
                file_path = seleccionado[0]

            # procesar la imagen con el método
                self.procesar(file_path)
            else:
            # no se seleccionó ningún archivo, realizar alguna acción o mostrar un mensaje de error
             return
        elif result == QFileDialog.Rejected:
            return
        
    def cargarpdf(self):
        file_dialog = QFileDialog()
        file_dialog.setNameFilter("PDF Files (*.pdf)")
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        if file_dialog.exec_():
            pdf_file_path = file_dialog.selectedFiles()[0]
            self.convertir(pdf_file_path)
        
    def convertir(self, pdf_file_path):
            
        images = convert_from_path(pdf_file_path)
        
        #convertir
        image = images[0].convert("RGB")
       #guardar en archivo temporal
        temp_image_path = "temp.jpg"
        image.save(temp_image_path, "JPEG")
        
       
        pixmap = QPixmap(temp_image_path)   #variable para asinar a label
        self.imagen_cargada = True #permitir subir csv
        self.Label_img.setPixmap(pixmap) #mostrar en label
        
        image.close() #quitar img temporal

    def procesar(self, image_path):  # método para leer la imagen y asignarla a variable imagen
        #dimensiones del label

        label_height = self.Label_img.height()
        qimagen = QImage(image_path)
        aspect_ratio = qimagen.width() / qimagen.height()
        target_width = int(label_height * aspect_ratio)
        scaled_image = qimagen.scaled(target_width, label_height, Qt.KeepAspectRatio)
        self.Label_img.setPixmap(QPixmap.fromImage(scaled_image))
        self.imagen_cargada = True
       
    def subircsv(self):
        if not self.imagen_cargada:
            QMessageBox.warning(self, "Error", "Antes debe ingresar un esquema")
            return
        
        
        file_dialog = QFileDialog()
        file_dialog.setNameFilters(["CSV Files (*.csv)", "All files (*)"])  #ver si es modificable
        file_dialog.selectNameFilter("CSV Files (*.csv)")
        #file_dialog.exec_()
        result = file_dialog.exec_()
        if result == QFileDialog.Accepted:
            file_path = file_dialog.selectedFiles()[0] #seleccionar y almacenar archivo

            df = pandas.read_csv(file_path, header=None)
            self.image_path = file_path #guardar en variable global
            qimage = self.Label_img.pixmap().toImage()  # obtener las dimensiones de la imagen
            
            qimage = qimage.convertToFormat(QImage.Format_RGB888)  # convertir la imagen a formato RGB888
            ancho = qimage.size().width()
            alto = qimage.size().height()
            #ancho = self.Label_img.width()
            #alto = self.Label_img.height()
            
            ancho_celda = ancho // len(df.columns)  # calcular ancho de celda dividiendo el ancho de la imagen por el número de columnas
            alto_celda = alto // len(df)  # calcular alto de la celda
            min_valor = df.min().min()
            max_valor = df.max().max()
            painter = QPainter() #variable painter para usar colores
            painter.begin(qimage) #estabelcerlo a la imagen
            

            colores = {     #colores disponibles con los codigos en rgb mas ordenados
                'color1': (0, 255, 0),
                'color2': (255, 165, 0),
                'color3': (255, 255, 0),
                'color4': (255, 0, 0)
            }

            painter.setOpacity(0.4) #cambiar opacidad para ver imagen de fondo (la mejor forma, simple y es solo una linea de cod)
            for fila_i, fila in df.iterrows():  # recorrer las filas del CSV
                for columna_i, valor in fila.items():  # recorrer las columnas
                    x = columna_i * (ancho_celda+1)  # ancho de la celda
                    y = (fila_i) * (alto_celda+1)  # alto de la celda (ahora no es necesario sumar 1)
                    # dibujar rectángulo
                    painter.fillRect(x, y, ancho_celda, alto_celda, Qt.white)
                    color_key = ''
                    if valor < min_valor + (max_valor - min_valor) / 4:
                        color_key = 'color1'
                    elif valor < min_valor + (max_valor - min_valor) * 2 / 4:
                        color_key = 'color2'
                    elif valor < min_valor + (max_valor - min_valor) * 3 / 4:
                        color_key = 'color3'
                    else:
                        color_key = 'color4'
                    
                    painter.fillRect(x, y, ancho_celda, alto_celda, QtGui.QColor(*colores[color_key])) #*necesario

                    # dibujar texto en la celda
                    painter.setPen(Qt.black)
                    painter.setFont(QFont("Arial", 10))

                    painter.drawText(x, y, ancho_celda, alto_celda, Qt.AlignCenter, str(valor))

            painter.end()
            #escalar csv a la imagen
            #escalar_img = QPixmap.fromImage(qimage).scaledToWidth(self.Label_img.width())  # escalar al ancho
            # escalar_img = QPixmap.fromImage(qimage).scaledToHeight(self.Label_img.height()) 
            escalar_img = QPixmap.fromImage(qimage).scaled(self.Label_img.size(), Qt.KeepAspectRatio)#, Qt.SmoothTransformation)
            
            self.Label_img.setPixmap(escalar_img)  

            
        elif result == QFileDialog.Rejected:
            return
        
    def guardar(self):
        img = self.Label_img.pixmap()  #Almacenar imagen del label en img
        if img is None:
            return
        save_path, _ = QFileDialog.getSaveFileName(self, "Guardar Imagen", "", "Images (*.png *.xpm *.jpg);;All Files (*)")
        if not save_path:
            return
        img.save(save_path)

    def recortar(self):

        # Obtener la ruta de la imagen que se encuentra en el label Label_img
        image_pixmap = self.Label_img.pixmap()
        if image_pixmap is None:
                return
        
        # Guardar la imagen en un archivo temporal
        temp_file_path = os.path.join(QDir.tempPath(), "temp_image.jpg")
        image_pixmap.save(temp_file_path)
        self.crop_window = ImageCropWindow(temp_file_path, self.Label_img,self) #Crear instancia como hijo de MainWindows
        self.crop_window.image_label.setPixmap(image_pixmap.scaled(self.Label_img.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))#
        self.crop_window.exec()
        
if __name__ == '__main__':
        app = QApplication([])
        window = MainWindow()
        window.show()
        app.exec_()
