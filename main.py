import sys
import os
import shutil
import xml.etree.ElementTree as ET
from datetime import datetime

from PySide6.QtWidgets import (QApplication, QMainWindow, QMessageBox, 
                               QProgressDialog, QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QLineEdit, QComboBox, QPushButton)
from PySide6.QtCore import (Qt, QTimer, QElapsedTimer, QObject, QThread, 
                            Signal, QTime, QLockFile, QSettings, QUrl)
from PySide6.QtGui import QDesktopServices

class ConfigManager:
    @staticmethod
    def load_settings():
        settings = QSettings("config.ini", QSettings.Format.IniFormat)
        if not settings.contains("Paths/SaidasCnc"):
            settings.setValue("Paths/AcervoSaidasCNC", "\\\\servidor\\PRODUCAO\\8. CONTROLE DE PRODUÇÃO\\1. SAÍDAS A CORTAR")
            settings.setValue("Paths/SaidasCnc", "\\\\servidor\\PRODUCAO\\1. SAÍDAS CNC")
            settings.setValue("Paths/SaidasCortadas", "\\\\servidor\\PRODUCAO\\8. CONTROLE DE PRODUÇÃO\\2. SAÍDAS CORTADAS")
            settings.setValue("Paths/PlanoCorte", "\\\\servidor\\PRODUCAO\\4. PLANO DE CORTE")
            settings.setValue("Paths/DadosXml", "\\\\servidor\\PRODUCAO\\8. CONTROLE DE PRODUÇÃO\\3. DADOS\\dados.xml")
            
    @staticmethod
    def get_server_path():
        settings = QSettings("config.ini", QSettings.Format.IniFormat)
        return settings.value("Paths/AcervoSaidasCNC", "\\\\servidor\\PRODUCAO\\8. CONTROLE DE PRODUÇÃO\\1. SAÍDAS A CORTAR")

    @staticmethod
    def get_saidas_cnc_path():
        settings = QSettings("config.ini", QSettings.Format.IniFormat)
        return settings.value("Paths/SaidasCnc", "\\\\servidor\\PRODUCAO\\1. SAÍDAS CNC")

    @staticmethod
    def get_saidas_cortadas_path():
        settings = QSettings("config.ini", QSettings.Format.IniFormat)
        return settings.value("Paths/SaidasCortadas", "\\\\servidor\\PRODUCAO\\8. CONTROLE DE PRODUÇÃO\\2. SAÍDAS CORTADAS")

    @staticmethod
    def get_k8_data_path():
        settings = QSettings("config.ini", QSettings.Format.IniFormat)
        return settings.value("Paths/DadosXml", "\\\\servidor\\PRODUCAO\\8. CONTROLE DE PRODUÇÃO\\3. DADOS\\dados.xml")

    @staticmethod
    def get_plano_corte_path():
        settings = QSettings("config.ini", QSettings.Format.IniFormat)
        return settings.value("Paths/PlanoCorte", "\\\\servidor\\PRODUCAO\\4. PLANO DE CORTE")


# --- THREAD DE BUSCA DE ARQUIVOS ---
class SearchFilesThread(QThread):
    finished_search = Signal(list)
    progress_update = Signal(int, int) # progresso, total
    
    def __init__(self, pedido, tipo, base_path):
        super().__init__()
        self.pedido = pedido
        self.tipo = tipo
        self.base_path = base_path
        self._is_canceled = False
        
    def cancel(self):
        self._is_canceled = True

    def run(self):
        results = []
        try:
            files = [f for f in os.listdir(self.base_path) if f.lower().endswith(".cnc")]
        except Exception:
            self.finished_search.emit(results)
            return

        total = len(files)
        prefix = ""
        if self.tipo == "Pedido": prefix = "P"
        elif self.tipo == "Avulso": prefix = "A"
        elif self.tipo == "Estoque": prefix = "E"
        elif self.tipo == "PPD": prefix = "PPD"
        elif self.tipo == "Reforma": prefix = "R"
        else:
            self.finished_search.emit(results)
            return

        for i, filename in enumerate(files):
            if self._is_canceled:
                break
            
            parts = filename.split('_')
            for part in parts:
                if part.startswith(prefix) and part[1:] == self.pedido:
                    results.append(filename)
                    break
                    
            if i % 10 == 0:  # Evita sobrecarregar a UI com milhoes de sinais
                self.progress_update.emit(i+1, total)

        self.progress_update.emit(total, total)
        if not self._is_canceled:
            self.finished_search.emit(results)


# --- THREAD DE BUSCA RECURSIVA DO PDF ---
class SearchPdfThread(QThread):
    finished_search = Signal(str)
    
    def __init__(self, pdf_filename, start_path):
        super().__init__()
        self.pdf_filename = pdf_filename
        self.start_path = start_path
        self._is_canceled = False
        
    def cancel(self):
        self._is_canceled = True

    def run(self):
        found_path = ""
        for root, dirs, files in os.walk(self.start_path):
            if self._is_canceled:
                break
            if self.pdf_filename in files:
                found_path = os.path.join(root, self.pdf_filename)
                break
                
        self.finished_search.emit(found_path)


# --- THREAD DE OPERAÇÃO DE ARQUIVO (Copiar/Mover) ---
class FileOperationThread(QThread):
    finished_op = Signal(str) # String vazia é sucesso, preenchida é erro
    
    def __init__(self, op_type, src, dst):
        super().__init__()
        self.op_type = op_type # "COPY" or "MOVE"
        self.src = src
        self.dst = dst
        
    def run(self):
        try:
            if self.op_type == "COPY":
                shutil.copy2(self.src, self.dst)
            elif self.op_type == "MOVE":
                shutil.move(self.src, self.dst)
            self.finished_op.emit("")
        except Exception as e:
            self.finished_op.emit(f"Falha na operação: {str(e)}")


# --- MAIN WINDOW ---
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Controle de Corte e Dobra")
        self.resize(800, 500)
        
        ConfigManager.load_settings()

        self.setup_ui()

        # Configurações de Estado Interno
        self.elapsed_timer = QElapsedTimer()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer_display)
        
        self.labelTimer.setText("00:00:00")
        
        # Conexões
        self.linePedido.editingFinished.connect(self.on_linePedido_editingFinished)
        self.pushButtonIniciar.clicked.connect(self.on_pushButtonIniciar_clicked)
        self.pushButtonFinalizar.clicked.connect(self.on_pushButtonFinalizar_clicked)
        self.pushButtonAbrirPDF.clicked.connect(self.on_pushButtonAbrirPDF_clicked)
        
        self.pushButtonFinalizar.setEnabled(False)
        
        # Estruturas assíncronas --------------------------
        self.search_thread = None
        self.pdf_thread = None
        self.file_op_thread = None
        
        self.progress_dialog = QProgressDialog("Aguarde...", "Cancelar", 0, 0, self)
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.setAutoClose(False)
        self.progress_dialog.setMinimumDuration(0)
        self.progress_dialog.canceled.connect(self.on_cancel_search)

    def setup_ui(self):
        """Constrói a interface nativamente no Python, substituindo o arquivo .ui"""
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(25)
        
        # === LINHA 1 ===
        row1_layout = QHBoxLayout()
        row1_layout.setSpacing(20)
        
        # Operador
        vbox_operador = QVBoxLayout()
        vbox_operador.addWidget(QLabel("Operador"))
        self.lineOperador = QLineEdit()
        vbox_operador.addWidget(self.lineOperador)
        row1_layout.addLayout(vbox_operador)
        
        # Máquina
        vbox_maquina = QVBoxLayout()
        vbox_maquina.addWidget(QLabel("Máquina"))
        self.cbox_Maquina = QComboBox()
        self.cbox_Maquina.addItems(["Bodor1 (12K)", "Bodor2 (6K)", "Dardi"])
        vbox_maquina.addWidget(self.cbox_Maquina)
        row1_layout.addLayout(vbox_maquina)
        
        # Tipo de Pedido
        vbox_tipo = QVBoxLayout()
        vbox_tipo.addWidget(QLabel("Tipo de pedido"))
        self.cbox_Tipo = QComboBox()
        self.cbox_Tipo.addItems(["Avulso", "Estoque", "Pedido", "Reforma", "PPD"])
        vbox_tipo.addWidget(self.cbox_Tipo)
        row1_layout.addLayout(vbox_tipo)
        
        # Número do Pedido
        vbox_pedido = QVBoxLayout()
        vbox_pedido.addWidget(QLabel("Número de Pedido"))
        self.linePedido = QLineEdit()
        vbox_pedido.addWidget(self.linePedido)
        row1_layout.addLayout(vbox_pedido)
        
        main_layout.addLayout(row1_layout)
        
        # === LINHA 2 ===
        row2_layout = QHBoxLayout()
        row2_layout.setSpacing(20)
        
        # Retalho
        vbox_retalho = QVBoxLayout()
        vbox_retalho.addWidget(QLabel("Chapa ou Retalho?"))
        self.cbox_Retalho = QComboBox()
        self.cbox_Retalho.addItems(["Chapa Inteira", "Retalho"])
        vbox_retalho.addWidget(self.cbox_Retalho)
        row2_layout.addLayout(vbox_retalho)
        
        # Saída CNC
        vbox_saida = QVBoxLayout()
        vbox_saida.addWidget(QLabel("Saída CNC a cortar"))
        self.comboBox = QComboBox()
        vbox_saida.addWidget(self.comboBox)
        
        # Botão PDF
        self.pushButtonAbrirPDF = QPushButton("Abrir PDF")
        self.pushButtonAbrirPDF.setFixedWidth(150)
        vbox_saida.addWidget(self.pushButtonAbrirPDF)
        
        row2_layout.addLayout(vbox_saida)
        row2_layout.setStretch(1, 4) # Dá largura extra ao comboBox de arquivos
        
        main_layout.addLayout(row2_layout)
        
        main_layout.addStretch() # Empurra botões para baixo
        
        # === LINHA 3 (AÇÕES E TIMER) ===
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()
        
        vbox_actions = QVBoxLayout()
        vbox_actions.setSpacing(10)
        
        self.labelTimer = QLabel("00:00:00")
        self.labelTimer.setObjectName("labelTimer") # Para CSS
        self.labelTimer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vbox_actions.addWidget(self.labelTimer)
        
        btns_layout = QHBoxLayout()
        self.pushButtonIniciar = QPushButton("INICIAR")
        self.pushButtonIniciar.setObjectName("pushButtonIniciar")
        self.pushButtonFinalizar = QPushButton("FINALIZAR")
        self.pushButtonFinalizar.setObjectName("pushButtonFinalizar")
        
        btns_layout.addWidget(self.pushButtonIniciar)
        btns_layout.addWidget(self.pushButtonFinalizar)
        
        vbox_actions.addLayout(btns_layout)
        bottom_layout.addLayout(vbox_actions)
        
        main_layout.addLayout(bottom_layout)

    def update_timer_display(self):
        elapsed = self.elapsed_timer.elapsed()
        qtime = QTime(0, 0, 0).addMSecs(elapsed)
        self.labelTimer.setText(qtime.toString("hh:mm:ss"))

    def on_linePedido_editingFinished(self):
        pedido = self.linePedido.text()
        if pedido:
            self.search_files(pedido)

    def search_files(self, pedido):
        self.comboBox.clear()
        self.comboBox.setEnabled(False)
        self.pushButtonIniciar.setEnabled(False)
        
        self.progress_dialog.setLabelText("Buscando arquivos Cnc...")
        self.progress_dialog.setMaximum(0)
        self.progress_dialog.setValue(0)
        self.progress_dialog.show()
        
        tipo = self.cbox_Tipo.currentText()
        base_path = ConfigManager.get_saidas_cnc_path()
        
        self.search_thread = SearchFilesThread(pedido, tipo, base_path)
        self.search_thread.progress_update.connect(self.on_search_progress)
        self.search_thread.finished_search.connect(self.on_search_finished)
        self.search_thread.start()

    def on_search_progress(self, current, total):
        self.progress_dialog.setMaximum(total)
        self.progress_dialog.setValue(current)

    def on_search_finished(self, results):
        self.progress_dialog.hide()
        self.comboBox.addItems(results)
        self.comboBox.setEnabled(True)
        self.pushButtonIniciar.setEnabled(True)
        
        if not results:
            QMessageBox.information(self, "Aviso", "Não foi encontrada nenhuma saída CNC para este pedido.")

    def on_cancel_search(self):
        if self.search_thread and self.search_thread.isRunning():
            self.search_thread.cancel()
            self.progress_dialog.setLabelText("Cancelando Busca...")

        if self.pdf_thread and self.pdf_thread.isRunning():
            self.pdf_thread.cancel()
            self.progress_dialog.setLabelText("Cancelando Busca...")


    # ======= FLUXO INICIAR (Grava Entrada no XML e Copia) =======
    def on_pushButtonIniciar_clicked(self):
        saida = self.comboBox.currentText()
        if not saida:
            return
            
        self.elapsed_timer.start()
        self.timer.start(1000)

        self._toggle_ui(False)
        self.pushButtonFinalizar.setEnabled(True)

        pedido = self.linePedido.text()
        operador = self.lineOperador.text()
        maquina = self.cbox_Maquina.currentText()
        retalho = self.cbox_Retalho.currentText()
        tipo = self.cbox_Tipo.currentText()
        dt_inicio = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        file_path = ConfigManager.get_k8_data_path()
        lock_file = QLockFile(file_path + ".lock")
        lock_file.setStaleLockTime(5000)
        
        # Manipula o XML com File Locking
        if lock_file.tryLock(2000):
            try:
                if not os.path.exists(file_path):
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<Dados>\n</Dados>")
                
                with open(file_path, "r", encoding="utf-8") as f:
                    xml_content = f.read()
                
                pos = xml_content.rfind("</Dados>")
                if pos != -1:
                    novo_no = f"<Entrada><Pedido>{pedido}</Pedido><Operador>{operador}</Operador><Maquina>{maquina}</Maquina><ChapaRetalho>{retalho}</ChapaRetalho><Saida>{saida}</Saida><Tipo>{tipo}</Tipo><DataHoraInicio>{dt_inicio}</DataHoraInicio></Entrada>\n"
                    xml_content = xml_content[:pos] + novo_no + xml_content[pos:]
                    
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(xml_content)
            except Exception as e:
                QMessageBox.warning(self, "Erro", f"Erro ao acessar banco XML: {e}")
            finally:
                lock_file.unlock()
        else:
            QMessageBox.warning(self, "Erro", "O banco de dados XML está ocupado por outro pc na rede. Tente de novo.")
            return

        # Copiar arquivo
        src_path = os.path.join(ConfigManager.get_server_path(), saida)
        dst_path = os.path.join(ConfigManager.get_saidas_cnc_path(), saida)
        
        self.progress_dialog.setLabelText("Copiando arquivo CNC...")
        self.progress_dialog.setMaximum(0)
        self.progress_dialog.show()
        
        self.file_op_thread = FileOperationThread("COPY", src_path, dst_path)
        self.file_op_thread.finished_op.connect(lambda err: self.on_file_op_finished(err, "Cópia concluída!"))
        self.file_op_thread.start()


    # ======= FLUXO FINALIZAR (Grava Término no XML e Move) =======
    def on_pushButtonFinalizar_clicked(self):
        self.timer.stop()
        elapsed = self.elapsed_timer.elapsed()
        qtime = QTime(0, 0, 0).addMSecs(elapsed)
        self.labelTimer.setText(qtime.toString("hh:mm:ss"))
        
        pedido = self.linePedido.text()
        saida = self.comboBox.currentText()
        if not saida: return
        
        dt_termino = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tempo_decorrido = qtime.toString("hh:mm:ss")
        
        file_path = ConfigManager.get_k8_data_path()
        lock_file = QLockFile(file_path + ".lock")
        lock_file.setStaleLockTime(5000)
        
        if lock_file.tryLock(2000):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    xml_content = f.read()

                # Achar a marca do pedido para injetar o termino!
                tag_str = f"<Pedido>{pedido}</Pedido>"
                pos = xml_content.rfind(tag_str)
                if pos != -1:
                    end_pos = xml_content.find("</Entrada>", pos)
                    if end_pos != -1:
                        novos_dados = f"<DataHoraTermino>{dt_termino}</DataHoraTermino><TempoDecorrido>{tempo_decorrido}</TempoDecorrido>"
                        xml_content = xml_content[:end_pos] + novos_dados + xml_content[end_pos:]
                        
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(xml_content)
            except Exception as e:
                QMessageBox.warning(self, "Erro XML", f"{e}")
            finally:
                lock_file.unlock()
        else:
            QMessageBox.warning(self, "Erro", "Banco XML bloqueado no momento de finalizar. Finalize de novo.")
            return

        # MOVER
        src_path = os.path.join(ConfigManager.get_saidas_cnc_path(), saida)
        dst_path = os.path.join(ConfigManager.get_saidas_cortadas_path(), saida)
        
        self.progress_dialog.setLabelText("Movendo arquivo CNC de volta...")
        self.progress_dialog.setMaximum(0)
        self.progress_dialog.show()

        self.file_op_thread = FileOperationThread("MOVE", src_path, dst_path)
        self.file_op_thread.finished_op.connect(lambda err: self.on_file_op_finished(err, "Corte Finalizado com sucesso!"))
        self.file_op_thread.start()


    def on_file_op_finished(self, err_msg, title="Sucesso"):
        self.progress_dialog.hide()
        self._toggle_ui(True)
        self.pushButtonFinalizar.setEnabled(False)
        
        if err_msg:
            QMessageBox.warning(self, "Aviso de Rede", err_msg)
        else:
            QMessageBox.information(self, "Sucesso", title)


    def on_pushButtonAbrirPDF_clicked(self):
        saida = self.comboBox.currentText()
        if not saida: return
        
        # Remove o "_SXX" final para abrir PDF
        pdf_name = saida.split("_S")[0] + ".pdf"
        
        self.progress_dialog.setLabelText("Procurando PDF na Rede...")
        self.progress_dialog.setMaximum(0)
        self.progress_dialog.show()
        
        search_path = ConfigManager.get_plano_corte_path()
        self.pdf_thread = SearchPdfThread(pdf_name, search_path)
        self.pdf_thread.finished_search.connect(self.on_pdf_search_finished)
        self.pdf_thread.start()


    def on_pdf_search_finished(self, found_path):
        self.progress_dialog.hide()
        if not found_path:
            QMessageBox.warning(self, "Não Encontrado", "O arquivo PDF correspondente não foi encontrado na base.")
        else:
            QDesktopServices.openUrl(QUrl.fromLocalFile(found_path))

    def _toggle_ui(self, enabled):
        self.linePedido.setEnabled(enabled)
        self.lineOperador.setEnabled(enabled)
        self.cbox_Maquina.setEnabled(enabled)
        self.cbox_Retalho.setEnabled(enabled)
        self.comboBox.setEnabled(enabled)
        self.pushButtonIniciar.setEnabled(enabled)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Carrega estilo do CSS
    if os.path.exists("style.css"):
        with open("style.css", "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
            
    w = MainWindow()
    w.show()
    sys.exit(app.exec())
