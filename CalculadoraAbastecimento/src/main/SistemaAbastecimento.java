/**
 * 
 */
package main;

import javax.swing.JOptionPane;

import util.CalculadoraLitrosAbastecidos;

public class SistemaAbastecimento {

	
	public static void main(String[] args) {
		
		// INICIA O SISTEMA DE ABASTECIMENTO
			iniciarSistema();
	}
	
	public static void iniciarSistema() {
		
		//MENSSAGEM DE BOAS VINDAS
		JOptionPane.showMessageDialog(null, "Inicie o Calculo de Litros Abastecidos");
		
		//CHAMA A CLASSE CALCULADORALITROSABASTECIDOS
		CalculadoraLitrosAbastecidos.main(null);
		
		//MENSSAGEM DE ENCERRAMENTO
		JOptionPane.showMessageDialog(null, "Encerrando o Sistema");
	}
	

}
