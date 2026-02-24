#include "mainwindow.h"
#include "ui_mainwindow.h"

#include <QFile>
#include <QXmlStreamWriter>
#include <QXmlStreamReader>
#include <QMessageBox>
#include <QDateTime>
#include <QDir>
#include <QComboBox>
#include <QFileInfo>
#include <QDesktopServices>
#include <QElapsedTimer> // Incluir a classe para o timer
#include <QLabel>
#include <QTimer>
#include <QSaveFile>
#include <QtConcurrent/QtConcurrentRun>
#include <QFuture>


MainWindow::MainWindow(QWidget *parent)
    : QMainWindow(parent)
    , ui(new Ui::MainWindow)
    , timer(new QTimer(this))
{
    ui->setupUi(this);

    // Inicializar watcher e dialog de progresso para buscas assíncronas
    searchWatcher = new QFutureWatcher<QStringList>(this);
    progressDialog = new QProgressDialog("Buscando arquivos...", "Cancelar", 0, 0, this);
    progressDialog->setWindowModality(Qt::WindowModal);
    progressDialog->setAutoClose(false);
    connect(searchWatcher, &QFutureWatcher<QStringList>::finished, this, &MainWindow::onSearchFinished);
    connect(progressDialog, &QProgressDialog::canceled, this, &MainWindow::onCancelSearch);

    // watcher para busca recursiva de PDF
    pdfWatcher = new QFutureWatcher<QString>(this);
    connect(pdfWatcher, &QFutureWatcher<QString>::finished, this, &MainWindow::onPdfSearchFinished);

    progressPoller = new QTimer(this);
    progressPoller->setInterval(200);
    connect(progressPoller, &QTimer::timeout, this, &MainWindow::onProgressTimeout);

    searchCanceled.store(false);
    searchProgress.store(0);
    searchTotal.store(0);

    labelTimer = ui->labelTimer;
    labelTimer->setText("00:00:00");

    connect(ui->linePedido, &QLineEdit::editingFinished, this, &MainWindow::on_linePedido_editingFinished);
    connect(timer, &QTimer::timeout, this, &MainWindow::updateTimerDisplay);

    // Conectar a mudança de tipo à função de pesquisa
    connect(ui->cbox_Tipo, QOverload<int>::of(&QComboBox::currentIndexChanged), [this]() {
        QString pedido = ui->linePedido->text();
        if (!pedido.isEmpty()) {
            searchFiles(pedido);
        }
    });

    ui->pushButtonFinalizar->setEnabled(false);
}



void MainWindow::updateTimerDisplay()
{
    // Calcula o tempo decorrido desde que o timer foi iniciado
    qint64 elapsed = elapsedTimer.elapsed();

    // Converte o tempo decorrido em horas, minutos e segundos
    QTime time(0, 0, 0);
    time = time.addMSecs(elapsed);

    // Atualiza o QLabel com o tempo decorrido
    labelTimer->setText(time.toString("hh:mm:ss"));
}


MainWindow::~MainWindow()
{
    delete ui;
}

// Slot chamado quando o usuário termina de editar o campo Pedido
void MainWindow::on_linePedido_editingFinished()
{
    QString pedido = ui->linePedido->text();
    if (!pedido.isEmpty()) {
        searchFiles(pedido);
    }
}

void MainWindow::searchFiles(const QString &pedido)
{
    // Executa a busca de forma assíncrona para não bloquear a UI
    ui->comboBox->clear();
    ui->comboBox->setEnabled(false);
    ui->pushButtonIniciar->setEnabled(false);
    // preparar estado para nova busca
    searchCanceled.store(false);
    searchProgress.store(0);
    searchTotal.store(0);
    progressDialog->setLabelText("Buscando arquivos...");
    progressDialog->setMaximum(0);
    progressDialog->show();
    progressPoller->start();

    QString tipo = ui->cbox_Tipo->currentText();
    QFuture<QStringList> future = QtConcurrent::run([=]{ return this->performSearchFiles(pedido, tipo); });
    searchWatcher->setFuture(future);
}

QStringList MainWindow::performSearchFiles(const QString &pedido, const QString &tipo)
{
    QStringList results;
    QDir dir("\\\\servidor\\PRODUCAO\\8. CONTROLE DE PRODUÇÃO\\1. SAÍDAS A CORTAR");
    QStringList filters;
    filters << "*.cnc";
    dir.setNameFilters(filters);
    QFileInfoList fileList = dir.entryInfoList();
    QString prefixo;

    // definir total para barra de progresso determinística
    searchTotal.store(fileList.size());
    searchProgress.store(0);

    if (tipo == "Pedido") {
        prefixo = "P";
    } else if (tipo == "Avulso") {
        prefixo = "A";
    } else if (tipo == "Estoque") {
        prefixo = "E";
    } else if (tipo == "PPD") {
        prefixo = "PPD";
    } else if (tipo == "Reforma") {
        prefixo = "R";
    } else {
        return results; // vazio
    }

    for (int i = 0; i < fileList.size(); ++i)
    {
        if (searchCanceled.load()) break; // cooperativo: respeitar cancelamento
        const QFileInfo &fileInfo = fileList.at(i);
        QString fileName = fileInfo.fileName();
        QStringList parts = fileName.split('_');

        foreach (const QString &part, parts)
        {
            if (part.startsWith(prefixo) && part.mid(1) == pedido)
            {
                results << fileName;
                break;
            }
        }
        searchProgress.fetch_add(1);
    }

    // marcar progresso como completo
    searchProgress.store(searchTotal.load());
    return results;
}

void MainWindow::onSearchFinished()
{
    QStringList results = searchWatcher->result();
    progressPoller->stop();
    progressDialog->hide();
    ui->comboBox->clear();
    ui->comboBox->addItems(results);
    ui->comboBox->setEnabled(true);
    ui->pushButtonIniciar->setEnabled(true);
    if (results.isEmpty()) {
        QMessageBox::information(this, "Aviso", "Não foi encontrada nenhuma saída CNC para este pedido.");
    }
}

void MainWindow::onCancelSearch()
{
    searchCanceled.store(true);
    progressDialog->setLabelText("Cancelando...");
    progressDialog->setCancelButtonText(QString());
}

void MainWindow::onProgressTimeout()
{
    int total = searchTotal.load();
    int prog = searchProgress.load();
    if (total > 0) {
        progressDialog->setMaximum(total);
        progressDialog->setValue(prog);
    } else {
        progressDialog->setMaximum(0);
    }
}




void MainWindow::on_pushButtonIniciar_clicked()
{
    // Iniciar o timer
    elapsedTimer->start();
    timer->start(1000);

    // Desabilitar os campos para edição e habilitar o botão de finalizar
    ui->linePedido->setEnabled(false);
    ui->lineOperador->setEnabled(false);
    ui->cbox_Maquina->setEnabled(false);
    ui->cbox_Retalho->setEnabled(false);
    ui->comboBox->setEnabled(false);
    ui->pushButtonIniciar->setEnabled(false);
    ui->pushButtonFinalizar->setEnabled(true);

    QString Pedido = ui->linePedido->text();  // Número de Pedido
    QString Operador = ui->lineOperador->text();  // Operador da máquina
    QString Maquina = ui->cbox_Maquina->currentText();  // Máquina utilizada
    QString Retalho = ui->cbox_Retalho->currentText();  // Se utiliza chapa ou retalho
    QString Saida = ui->comboBox->currentText(); // Nome da saída selecionada
    QString Tipo = ui->cbox_Tipo->currentText(); // Tipo selecionado

    // Obtenha a data e hora atuais
    QString dataHoraInicio = QDateTime::currentDateTime().toString("yyyy-MM-dd HH:mm:ss");
    // Salvar as informações iniciais no XML de forma segura com QSaveFile
    QString filePath = "\\\\servidor\\PRODUCAO\\8. CONTROLE DE PRODUÇÃO\\3. DADOS\\dados.xml";
    QString xmlContent;
    QFile existing(filePath);
    if (existing.open(QIODevice::ReadOnly | QIODevice::Text)) {
        xmlContent = existing.readAll();
        existing.close();
    } else {
        xmlContent = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<Dados>\n</Dados>";
    }

    int pos = xmlContent.lastIndexOf("</Dados>");
    if (pos != -1) {
        xmlContent.insert(pos, QString("<Entrada><Pedido>%1</Pedido><Operador>%2</Operador><Maquina>%3</Maquina><ChapaRetalho>%4</ChapaRetalho><Saida>%5</Saida><Tipo>%6</Tipo><DataHoraInicio>%7</DataHoraInicio></Entrada>\n")
                          .arg(Pedido)
                          .arg(Operador)
                          .arg(Maquina)
                          .arg(Retalho)
                          .arg(Saida)
                          .arg(Tipo)
                          .arg(dataHoraInicio));
    }

    QSaveFile saveFile(filePath);
    if (!saveFile.open(QIODevice::WriteOnly | QIODevice::Text)) {
        QMessageBox::warning(this, "Erro", "Não foi possível abrir o arquivo XML para escrita");
        return;
    }
    QTextStream out(&saveFile);
    out << xmlContent;
    if (!saveFile.commit()) {
        QMessageBox::warning(this, "Erro", "Falha ao gravar o arquivo XML (commit falhou)");
        return;
    }



    // Mover o arquivo selecionado na QComboBox para a pasta Saídas Selecionadas
    QString selectedFile = ui->comboBox->currentText();
    if (!selectedFile.isEmpty()) {
        QString sourcePath = "\\\\servidor\\PRODUCAO\\8. CONTROLE DE PRODUÇÃO\\1. SAÍDAS A CORTAR\\" + selectedFile;
        QString destinationPath = "\\\\servidor\\PRODUCAO\\1. SAÍDAS CNC\\" + selectedFile;

        if (QFile::exists(destinationPath)) {
            QFile::remove(destinationPath); // Remove o arquivo existente se houver
        }
        if (QFile::copy(sourcePath, destinationPath)) {
            QMessageBox::information(this, "Sucesso", "Plano iniciado com sucesso!");
        } else {
            QMessageBox::warning(this, "Erro", "Não foi possível mover o arquivo.");
        }

    }
}

void MainWindow::on_pushButtonFinalizar_clicked()
{
    // Parar o QTimer para interromper as atualizações
    timer->stop();

    // Calcular o tempo decorrido final
    qint64 elapsed = elapsedTimer->elapsed();
    QTime time(0, 0, 0);
    time = time.addMSecs(elapsed);
    labelTimer->setText(time.toString("hh:mm:ss"));  // Exibir o tempo decorrido final no label

    QString Pedido = ui->linePedido->text();
    QString selectedFile = ui->comboBox->currentText();
    QString Tipo = ui->cbox_Tipo->currentData().toString(); // Tipo selecionado

    // Obtenha a data e hora atuais
    QString dataHoraTermino = QDateTime::currentDateTime().toString("yyyy-MM-dd HH:mm:ss");

    // Obter o tempo total decorrido
    QString tempoDecorrido = time.toString("hh:mm:ss");

    // Atualizar as informações de finalização no XML usando QSaveFile
    {
        QString filePath = "\\\\servidor\\PRODUCAO\\8. CONTROLE DE PRODUÇÃO\\3. DADOS\\dados.xml";
        QFile existing(filePath);
        QString xmlContent;
        if (existing.open(QIODevice::ReadOnly | QIODevice::Text)) {
            xmlContent = existing.readAll();
            existing.close();
        } else {
            QMessageBox::warning(this, "Erro", "Não foi possível abrir o arquivo XML");
            return;
        }

        int pos = xmlContent.lastIndexOf("<Pedido>" + Pedido + "</Pedido>");
        if (pos != -1) {
            int endPos = xmlContent.indexOf("</Entrada>", pos);
            if (endPos != -1) {
                xmlContent.insert(endPos, QString("<DataHoraTermino>%1</DataHoraTermino><TempoDecorrido>%2</TempoDecorrido>")
                                      .arg(dataHoraTermino)
                                      .arg(tempoDecorrido));
            }
        }

        QSaveFile saveFile(filePath);
        if (!saveFile.open(QIODevice::WriteOnly | QIODevice::Text)) {
            QMessageBox::warning(this, "Erro", "Não foi possível abrir o arquivo XML para escrita");
            return;
        }
        QTextStream out(&saveFile);
        out << xmlContent;
        if (!saveFile.commit()) {
            QMessageBox::warning(this, "Erro", "Falha ao gravar o arquivo XML (commit falhou)");
            return;
        }
    }



    // Mover o arquivo selecionado para a pasta Saídas Cortadas
    if (!selectedFile.isEmpty()) {
        QString sourcePath = "\\\\servidor\\PRODUCAO\\1. SAÍDAS CNC\\" + selectedFile;
        QString destinationPath = "\\\\servidor\\PRODUCAO\\8. CONTROLE DE PRODUÇÃO\\2. SAÍDAS CORTADAS\\" + selectedFile;

        if (QFile::exists(destinationPath)) {
            QFile::remove(destinationPath); // Remove o arquivo existente se houver
        }
        if (QFile::rename(sourcePath, destinationPath)) {
            QMessageBox::information(this, "Sucesso", "Plano finalizado com sucesso!");
        } else {
            QMessageBox::warning(this, "Erro", "Não foi possível mover o arquivo.");
        }

    }

    // Reativar os campos para nova entrada
    ui->linePedido->setEnabled(true);
    ui->lineOperador->setEnabled(true);
    ui->cbox_Maquina->setEnabled(true);
    ui->cbox_Retalho->setEnabled(true);
    ui->comboBox->setEnabled(true);
    ui->pushButtonIniciar->setEnabled(true);
    ui->pushButtonFinalizar->setEnabled(false);
}


void MainWindow::on_pushButtonAbrirPDF_clicked()
{
    QString saida = ui->comboBox->currentText(); // Obtém a saída selecionada

    if (saida.isEmpty()) {
        QMessageBox::warning(this, "Erro", "Nenhuma saída foi selecionada.");
        return;
    }

    // Extrai a parte antes do "_S" para encontrar o PDF correspondente
    QString pdfFileName = saida.split("_S").first() + ".pdf";
    QString searchPath = "\\\\servidor\\PRODUCAO\\4. PLANO DE CORTE\\";

    // Inicia busca assíncrona do PDF (recursiva) com cancelamento/progresso
    searchCanceled.store(false);
    searchProgress.store(0);
    searchTotal.store(0);
    progressDialog->setLabelText("Buscando PDF...");
    progressDialog->setMaximum(0);
    progressDialog->show();
    progressPoller->start();

    QFuture<QString> future = QtConcurrent::run([=]{ return this->performSearchPdf(pdfFileName, searchPath); });
    pdfWatcher->setFuture(future);
}

QString MainWindow::performSearchPdf(const QString &pdfFileName, const QString &searchPath)
{
    QString foundPath;
    QStringList stack;
    stack << searchPath;

    while (!stack.isEmpty() && !searchCanceled.load()) {
        QString path = stack.takeLast();
        QDir directory(path);
        QFileInfoList list = directory.entryInfoList(QDir::AllDirs | QDir::NoDotAndDotDot | QDir::Files, QDir::Name);
        for (const QFileInfo &info : list) {
            if (searchCanceled.load()) break;
            if (info.isFile()) {
                searchProgress.fetch_add(1);
                if (info.fileName() == pdfFileName) {
                    foundPath = info.absoluteFilePath();
                    return foundPath;
                }
            } else if (info.isDir()) {
                stack << info.absoluteFilePath();
            }
        }
    }

    return QString();
}

void MainWindow::onPdfSearchFinished()
{
    progressPoller->stop();
    progressDialog->hide();
    QString result = pdfWatcher->result();
    if (result.isEmpty()) {
        if (searchCanceled.load()) {
            QMessageBox::information(this, "Aviso", "Busca cancelada.");
        } else {
            QMessageBox::warning(this, "Erro", "Arquivo PDF correspondente não encontrado.");
        }
    } else {
        QDesktopServices::openUrl(QUrl::fromLocalFile(result));
    }
}

