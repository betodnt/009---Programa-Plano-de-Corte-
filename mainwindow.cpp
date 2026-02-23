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


MainWindow::MainWindow(QWidget *parent)
    : QMainWindow(parent)
    , ui(new Ui::MainWindow)
    , elapsedTimer(new QElapsedTimer)
    , timer(new QTimer(this))
{
    ui->setupUi(this);

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
    qint64 elapsed = elapsedTimer->elapsed();

    // Converte o tempo decorrido em horas, minutos e segundos
    QTime time(0, 0, 0);
    time = time.addMSecs(elapsed);

    // Atualiza o QLabel com o tempo decorrido
    labelTimer->setText(time.toString("hh:mm:ss"));
}


MainWindow::~MainWindow()
{
    delete ui;
    delete elapsedTimer;
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
    QDir dir("\\\\servidor\\PRODUCAO\\8. CONTROLE DE PRODUÇÃO\\1. SAÍDAS A CORTAR");
    QStringList filters;
    filters << "*.cnc";
    dir.setNameFilters(filters);
    QFileInfoList fileList = dir.entryInfoList();

    ui->comboBox->clear(); // Limpa a lista suspensa antes de preencher

    // Identifica o prefixo baseado no tipo selecionado
    QString tipo = ui->cbox_Tipo->currentText();  // Supondo que a QComboBox de tipo se chama comboBoxTipo
    QString prefixo;

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
        QMessageBox::warning(this, "Erro", "Tipo de arquivo não reconhecido.");
        return;
    }

    foreach (const QFileInfo &fileInfo, fileList)
    {
        QString fileName = fileInfo.fileName();
        QStringList parts = fileName.split('_');

        // Procurar a parte que começa com o prefixo definido e comparar com o pedido
        foreach (const QString &part, parts)
        {
            if (part.startsWith(prefixo) && part.mid(1) == pedido)
            {
                ui->comboBox->addItem(fileName);
                break;
            }
        }
    }

    if (ui->comboBox->count() == 0) {
        QMessageBox::information(this, "Aviso", "Não foi encontrada nenhuma saída CNC para este pedido.");
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

    // Salvar as informações iniciais no XML
    QFile file("\\\\servidor\\PRODUCAO\\8. CONTROLE DE PRODUÇÃO\\3. DADOS\\dados.xml");
    if (!file.open(QIODevice::ReadWrite | QIODevice::Text))
    {
        QMessageBox::warning(this, "Erro", "Não foi possível abrir o arquivo XML");
        return;
    }

    QXmlStreamReader xmlReader(&file);
    QString xmlContent;

    // Verificar se o arquivo já contém conteúdo
    if (file.size() > 0)
    {
        // Ler o conteúdo existente
        xmlContent = file.readAll();
        file.resize(0);  // Esvazia o arquivo para escrever novamente
    }
    else
    {
        // Iniciar o arquivo XML se estiver vazio
        xmlContent = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<Dados>\n</Dados>";
    }

    file.close();

    // Reabrir o arquivo para escrita
    if (!file.open(QIODevice::WriteOnly | QIODevice::Text))
    {
        QMessageBox::warning(this, "Erro", "Não foi possível abrir o arquivo XML para escrita");
        return;
    }

    // Posicionar o ponteiro do arquivo antes da tag de fechamento </Dados>
    int pos = xmlContent.lastIndexOf("</Dados>");
    if (pos != -1)
    {
        xmlContent.insert(pos, QString("<Entrada><Pedido>%1</Pedido><Operador>%2</Operador><Maquina>%3</Maquina><ChapaRetalho>%4</ChapaRetalho><Saida>%5</Saida><Tipo>%6</Tipo><DataHoraInicio>%7</DataHoraInicio></Entrada>\n")
                              .arg(Pedido)
                              .arg(Operador)
                              .arg(Maquina)
                              .arg(Retalho)
                              .arg(Saida)
                              .arg(Tipo)
                              .arg(dataHoraInicio));
    }

    // Escrever o conteúdo atualizado de volta no arquivo
    QTextStream stream(&file);
    stream << xmlContent;



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

    // Atualizar as informações de finalização no XML
    QFile file("\\\\servidor\\PRODUCAO\\8. CONTROLE DE PRODUÇÃO\\3. DADOS\\dados.xml");
    if (!file.open(QIODevice::ReadWrite | QIODevice::Text))
    {
        QMessageBox::warning(this, "Erro", "Não foi possível abrir o arquivo XML");
        return;
    }

    QString xmlContent = file.readAll();
    file.resize(0);  // Esvazia o arquivo para escrever novamente

    int pos = xmlContent.lastIndexOf("<Pedido>" + Pedido + "</Pedido>");
    if (pos != -1) {
        int endPos = xmlContent.indexOf("</Entrada>", pos);
        if (endPos != -1) {
            xmlContent.insert(endPos, QString("<DataHoraTermino>%1</DataHoraTermino><TempoDecorrido>%2</TempoDecorrido>")
                                  .arg(dataHoraTermino)
                                  .arg(tempoDecorrido));
        }
    }

    // Escrever o conteúdo atualizado de volta no arquivo
    QTextStream stream(&file);
    stream << xmlContent;



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

    QDir dir(searchPath);
    QStringList filters;
    filters << pdfFileName;
    dir.setNameFilters(filters);
    dir.setFilter(QDir::Files | QDir::NoSymLinks | QDir::AllDirs);

    QFileInfoList entries = dir.entryInfoList(QDir::AllDirs | QDir::NoDotAndDotDot | QDir::Files, QDir::Name);
    bool fileFound = false;

    // Função recursiva para buscar o arquivo PDF
    std::function<void(const QString &)> searchRecursively = [&](const QString &path) {
        QDir directory(path);
        QFileInfoList list = directory.entryInfoList(QDir::AllDirs | QDir::NoDotAndDotDot | QDir::Files, QDir::Name);
        foreach (const QFileInfo &info, list) {
            if (info.isFile() && info.fileName() == pdfFileName) {
                QString pdfFilePath = info.absoluteFilePath();
                QDesktopServices::openUrl(QUrl::fromLocalFile(pdfFilePath));
                fileFound = true;
                return;
            } else if (info.isDir()) {
                searchRecursively(info.absoluteFilePath());
                if (fileFound) return;
            }
        }
    };

    searchRecursively(searchPath);

    if (!fileFound) {
        QMessageBox::warning(this, "Erro", "Arquivo PDF correspondente não encontrado.");
    }
}

