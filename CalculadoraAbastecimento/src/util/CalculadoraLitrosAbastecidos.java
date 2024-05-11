/**
 * 
 */
package util;

import javax.swing.JOptionPane;


public class CalculadoraLitrosAbastecidos {

	public static void main(String[] args) {
				// SOLICITA AO USUARIO QUE INFORME O VALOR TOTAL DO ABASTECIMENTO
		
				String valorTotalStr = JOptionPane.showInputDialog(null, "Digite o valor total Abastecido: ");
				double valorTotal = Double.parseDouble(valorTotalStr); 
				
				// SOLICITA AO USUARIO QUE INFORME O PREÇO POR LITRO
				
				String precoPorLitroStr = JOptionPane.showInputDialog(null, "Digite o Preço Por Litro: ");
				double precoPorLitro = Double.parseDouble(precoPorLitroStr);
				
				//CALCULA A QUANTIDADE DE LITROS ABASTECIDOS
				double litrosAbastecidos = valorTotal / precoPorLitro;
				
				//EXIBE O RESULTADO DO USUARIO
				JOptionPane.showMessageDialog(null, "A Quantidade de litros Abastecidos Foi: " + litrosAbastecidos );

	}

}
