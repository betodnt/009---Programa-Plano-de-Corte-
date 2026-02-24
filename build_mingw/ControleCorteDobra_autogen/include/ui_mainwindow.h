/********************************************************************************
** Form generated from reading UI file 'mainwindow.ui'
**
** Created by: Qt User Interface Compiler version 6.10.2
**
** WARNING! All changes made in this file will be lost when recompiling UI file!
********************************************************************************/

#ifndef UI_MAINWINDOW_H
#define UI_MAINWINDOW_H

#include <QtCore/QVariant>
#include <QtWidgets/QApplication>
#include <QtWidgets/QComboBox>
#include <QtWidgets/QLabel>
#include <QtWidgets/QLineEdit>
#include <QtWidgets/QMainWindow>
#include <QtWidgets/QPushButton>
#include <QtWidgets/QStatusBar>
#include <QtWidgets/QWidget>

QT_BEGIN_NAMESPACE

class Ui_MainWindow
{
public:
    QWidget *centralwidget;
    QLineEdit *lineOperador;
    QLineEdit *linePedido;
    QPushButton *pushButtonIniciar;
    QLabel *label;
    QLabel *label_2;
    QLabel *label_3;
    QLabel *label_4;
    QComboBox *cbox_Retalho;
    QComboBox *cbox_Maquina;
    QComboBox *comboBox;
    QLabel *label_5;
    QPushButton *pushButtonFinalizar;
    QPushButton *pushButtonAbrirPDF;
    QLabel *labelTimer;
    QComboBox *cbox_Tipo;
    QLabel *label_6;
    QStatusBar *statusbar;

    void setupUi(QMainWindow *MainWindow)
    {
        if (MainWindow->objectName().isEmpty())
            MainWindow->setObjectName("MainWindow");
        MainWindow->resize(800, 600);
        QPalette palette;
        QBrush brush(QColor(255, 255, 255, 255));
        brush.setStyle(Qt::BrushStyle::SolidPattern);
        palette.setBrush(QPalette::ColorGroup::Active, QPalette::ColorRole::WindowText, brush);
        palette.setBrush(QPalette::ColorGroup::Active, QPalette::ColorRole::Text, brush);
        QBrush brush1(QColor(43, 43, 43, 255));
        brush1.setStyle(Qt::BrushStyle::SolidPattern);
        palette.setBrush(QPalette::ColorGroup::Active, QPalette::ColorRole::Window, brush1);
        palette.setBrush(QPalette::ColorGroup::Inactive, QPalette::ColorRole::WindowText, brush);
        palette.setBrush(QPalette::ColorGroup::Inactive, QPalette::ColorRole::Text, brush);
        palette.setBrush(QPalette::ColorGroup::Inactive, QPalette::ColorRole::Window, brush1);
        palette.setBrush(QPalette::ColorGroup::Disabled, QPalette::ColorRole::Base, brush1);
        palette.setBrush(QPalette::ColorGroup::Disabled, QPalette::ColorRole::Window, brush1);
        MainWindow->setPalette(palette);
        MainWindow->setToolTipDuration(-1);
        centralwidget = new QWidget(MainWindow);
        centralwidget->setObjectName("centralwidget");
        QPalette palette1;
        palette1.setBrush(QPalette::ColorGroup::Active, QPalette::ColorRole::Text, brush);
        QBrush brush2(QColor(49, 49, 49, 255));
        brush2.setStyle(Qt::BrushStyle::SolidPattern);
        palette1.setBrush(QPalette::ColorGroup::Active, QPalette::ColorRole::Window, brush2);
        palette1.setBrush(QPalette::ColorGroup::Inactive, QPalette::ColorRole::Text, brush);
        palette1.setBrush(QPalette::ColorGroup::Inactive, QPalette::ColorRole::Window, brush2);
        palette1.setBrush(QPalette::ColorGroup::Disabled, QPalette::ColorRole::Base, brush2);
        palette1.setBrush(QPalette::ColorGroup::Disabled, QPalette::ColorRole::Window, brush2);
        centralwidget->setPalette(palette1);
        centralwidget->setAutoFillBackground(false);
        lineOperador = new QLineEdit(centralwidget);
        lineOperador->setObjectName("lineOperador");
        lineOperador->setGeometry(QRect(50, 50, 171, 21));
        QPalette palette2;
        QBrush brush3(QColor(0, 0, 0, 255));
        brush3.setStyle(Qt::BrushStyle::SolidPattern);
        palette2.setBrush(QPalette::ColorGroup::Active, QPalette::ColorRole::WindowText, brush3);
        palette2.setBrush(QPalette::ColorGroup::Active, QPalette::ColorRole::Text, brush3);
        palette2.setBrush(QPalette::ColorGroup::Inactive, QPalette::ColorRole::WindowText, brush3);
        palette2.setBrush(QPalette::ColorGroup::Inactive, QPalette::ColorRole::Text, brush3);
        lineOperador->setPalette(palette2);
        QFont font;
        font.setPointSize(12);
        lineOperador->setFont(font);
        linePedido = new QLineEdit(centralwidget);
        linePedido->setObjectName("linePedido");
        linePedido->setGeometry(QRect(590, 50, 91, 24));
        QPalette palette3;
        palette3.setBrush(QPalette::ColorGroup::Active, QPalette::ColorRole::WindowText, brush3);
        palette3.setBrush(QPalette::ColorGroup::Active, QPalette::ColorRole::Text, brush3);
        palette3.setBrush(QPalette::ColorGroup::Inactive, QPalette::ColorRole::WindowText, brush3);
        palette3.setBrush(QPalette::ColorGroup::Inactive, QPalette::ColorRole::Text, brush3);
        linePedido->setPalette(palette3);
        linePedido->setFont(font);
        pushButtonIniciar = new QPushButton(centralwidget);
        pushButtonIniciar->setObjectName("pushButtonIniciar");
        pushButtonIniciar->setGeometry(QRect(469, 373, 91, 31));
        pushButtonIniciar->setFont(font);
        label = new QLabel(centralwidget);
        label->setObjectName("label");
        label->setGeometry(QRect(50, 30, 91, 21));
        label->setFont(font);
        label_2 = new QLabel(centralwidget);
        label_2->setObjectName("label_2");
        label_2->setGeometry(QRect(260, 30, 81, 21));
        label_2->setFont(font);
        label_3 = new QLabel(centralwidget);
        label_3->setObjectName("label_3");
        label_3->setGeometry(QRect(590, 30, 131, 21));
        label_3->setFont(font);
        label_4 = new QLabel(centralwidget);
        label_4->setObjectName("label_4");
        label_4->setGeometry(QRect(50, 140, 131, 16));
        label_4->setFont(font);
        cbox_Retalho = new QComboBox(centralwidget);
        cbox_Retalho->addItem(QString());
        cbox_Retalho->addItem(QString());
        cbox_Retalho->setObjectName("cbox_Retalho");
        cbox_Retalho->setGeometry(QRect(50, 160, 131, 24));
        QPalette palette4;
        palette4.setBrush(QPalette::ColorGroup::Active, QPalette::ColorRole::WindowText, brush3);
        palette4.setBrush(QPalette::ColorGroup::Active, QPalette::ColorRole::Text, brush3);
        palette4.setBrush(QPalette::ColorGroup::Inactive, QPalette::ColorRole::WindowText, brush3);
        palette4.setBrush(QPalette::ColorGroup::Inactive, QPalette::ColorRole::Text, brush3);
        cbox_Retalho->setPalette(palette4);
        cbox_Retalho->setFont(font);
        cbox_Maquina = new QComboBox(centralwidget);
        cbox_Maquina->addItem(QString());
        cbox_Maquina->addItem(QString());
        cbox_Maquina->addItem(QString());
        cbox_Maquina->setObjectName("cbox_Maquina");
        cbox_Maquina->setGeometry(QRect(260, 50, 131, 24));
        QPalette palette5;
        palette5.setBrush(QPalette::ColorGroup::Active, QPalette::ColorRole::WindowText, brush3);
        palette5.setBrush(QPalette::ColorGroup::Active, QPalette::ColorRole::Text, brush3);
        palette5.setBrush(QPalette::ColorGroup::Inactive, QPalette::ColorRole::WindowText, brush3);
        palette5.setBrush(QPalette::ColorGroup::Inactive, QPalette::ColorRole::Text, brush3);
        cbox_Maquina->setPalette(palette5);
        cbox_Maquina->setFont(font);
        comboBox = new QComboBox(centralwidget);
        comboBox->setObjectName("comboBox");
        comboBox->setGeometry(QRect(240, 160, 501, 24));
        QPalette palette6;
        palette6.setBrush(QPalette::ColorGroup::Active, QPalette::ColorRole::WindowText, brush3);
        palette6.setBrush(QPalette::ColorGroup::Active, QPalette::ColorRole::Text, brush3);
        palette6.setBrush(QPalette::ColorGroup::Inactive, QPalette::ColorRole::WindowText, brush3);
        palette6.setBrush(QPalette::ColorGroup::Inactive, QPalette::ColorRole::Text, brush3);
        comboBox->setPalette(palette6);
        comboBox->setFont(font);
        label_5 = new QLabel(centralwidget);
        label_5->setObjectName("label_5");
        label_5->setGeometry(QRect(240, 140, 141, 16));
        label_5->setFont(font);
        pushButtonFinalizar = new QPushButton(centralwidget);
        pushButtonFinalizar->setObjectName("pushButtonFinalizar");
        pushButtonFinalizar->setGeometry(QRect(579, 373, 91, 31));
        pushButtonFinalizar->setFont(font);
        pushButtonAbrirPDF = new QPushButton(centralwidget);
        pushButtonAbrirPDF->setObjectName("pushButtonAbrirPDF");
        pushButtonAbrirPDF->setGeometry(QRect(240, 200, 91, 31));
        pushButtonAbrirPDF->setFont(font);
        labelTimer = new QLabel(centralwidget);
        labelTimer->setObjectName("labelTimer");
        labelTimer->setGeometry(QRect(580, 350, 71, 16));
        labelTimer->setFont(font);
        cbox_Tipo = new QComboBox(centralwidget);
        cbox_Tipo->addItem(QString());
        cbox_Tipo->addItem(QString());
        cbox_Tipo->addItem(QString());
        cbox_Tipo->addItem(QString());
        cbox_Tipo->addItem(QString());
        cbox_Tipo->setObjectName("cbox_Tipo");
        cbox_Tipo->setGeometry(QRect(420, 50, 131, 24));
        QPalette palette7;
        palette7.setBrush(QPalette::ColorGroup::Active, QPalette::ColorRole::WindowText, brush3);
        palette7.setBrush(QPalette::ColorGroup::Active, QPalette::ColorRole::Text, brush3);
        palette7.setBrush(QPalette::ColorGroup::Inactive, QPalette::ColorRole::WindowText, brush3);
        palette7.setBrush(QPalette::ColorGroup::Inactive, QPalette::ColorRole::Text, brush3);
        cbox_Tipo->setPalette(palette7);
        cbox_Tipo->setFont(font);
        label_6 = new QLabel(centralwidget);
        label_6->setObjectName("label_6");
        label_6->setGeometry(QRect(420, 30, 131, 21));
        label_6->setFont(font);
        MainWindow->setCentralWidget(centralwidget);
        statusbar = new QStatusBar(MainWindow);
        statusbar->setObjectName("statusbar");
        MainWindow->setStatusBar(statusbar);

        retranslateUi(MainWindow);

        QMetaObject::connectSlotsByName(MainWindow);
    } // setupUi

    void retranslateUi(QMainWindow *MainWindow)
    {
        MainWindow->setWindowTitle(QCoreApplication::translate("MainWindow", "MainWindow", nullptr));
        pushButtonIniciar->setText(QCoreApplication::translate("MainWindow", "INICIAR", nullptr));
        label->setText(QCoreApplication::translate("MainWindow", "Operador", nullptr));
        label_2->setText(QCoreApplication::translate("MainWindow", "M\303\241quina", nullptr));
        label_3->setText(QCoreApplication::translate("MainWindow", "N\303\272mero de Pedido", nullptr));
        label_4->setText(QCoreApplication::translate("MainWindow", "Chapa ou Retalho?", nullptr));
        cbox_Retalho->setItemText(0, QCoreApplication::translate("MainWindow", "Chapa Inteira", nullptr));
        cbox_Retalho->setItemText(1, QCoreApplication::translate("MainWindow", "Retalho", nullptr));

        cbox_Maquina->setItemText(0, QCoreApplication::translate("MainWindow", "Bodor1 (12K)", nullptr));
        cbox_Maquina->setItemText(1, QCoreApplication::translate("MainWindow", "Bodor2 (6K)", nullptr));
        cbox_Maquina->setItemText(2, QCoreApplication::translate("MainWindow", "Dardi", nullptr));

        label_5->setText(QCoreApplication::translate("MainWindow", "Sa\303\255da CNC a cortar", nullptr));
        pushButtonFinalizar->setText(QCoreApplication::translate("MainWindow", "FINALIZAR", nullptr));
        pushButtonAbrirPDF->setText(QCoreApplication::translate("MainWindow", "Abrir PDF", nullptr));
        labelTimer->setText(QCoreApplication::translate("MainWindow", "00:00:00", nullptr));
        cbox_Tipo->setItemText(0, QCoreApplication::translate("MainWindow", "Avulso", nullptr));
        cbox_Tipo->setItemText(1, QCoreApplication::translate("MainWindow", "Estoque", nullptr));
        cbox_Tipo->setItemText(2, QCoreApplication::translate("MainWindow", "Pedido", nullptr));
        cbox_Tipo->setItemText(3, QCoreApplication::translate("MainWindow", "Reforma", nullptr));
        cbox_Tipo->setItemText(4, QCoreApplication::translate("MainWindow", "PPD", nullptr));

        label_6->setText(QCoreApplication::translate("MainWindow", "Tipo de pedido", nullptr));
    } // retranslateUi

};

namespace Ui {
    class MainWindow: public Ui_MainWindow {};
} // namespace Ui

QT_END_NAMESPACE

#endif // UI_MAINWINDOW_H
