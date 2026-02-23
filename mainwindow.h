#ifndef MAINWINDOW_H
#define MAINWINDOW_H

#include <QMainWindow>
#include <QElapsedTimer>
#include <QTimer>     // Incluir QTimer para atualizações periódicas
#include <QLabel>     // Incluir QLabel para exibir o tempo
#include <QSpinBox>   // Incluir QSpinBox para definir o número de cortes

QT_BEGIN_NAMESPACE
namespace Ui { class MainWindow; }
QT_END_NAMESPACE

class MainWindow : public QMainWindow
{
    Q_OBJECT

public:
    MainWindow(QWidget *parent = nullptr);
    ~MainWindow();

private slots:
    void on_linePedido_editingFinished();
    void searchFiles(const QString &pedido);
    void on_pushButtonIniciar_clicked();
    void on_pushButtonFinalizar_clicked();
    void on_pushButtonAbrirPDF_clicked(); // Função para abrir o PDF
    void updateTimerDisplay();             // Slot para atualizar o display do timer


private:
    Ui::MainWindow *ui;
    QElapsedTimer *elapsedTimer;  // Timer para medir o tempo decorrido
    QTimer *timer;                // Timer para atualização do display em tempo real
    QLabel *labelTimer;           // QLabel para exibir o tempo
};

#endif // MAINWINDOW_H
