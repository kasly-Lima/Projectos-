/**
 * 
 */

import javax.swing.JOptionPane;

/**
 * 
 */
public class arrayPrimitivo {

	/**
	 * @param args
	 */
	public static void main(String[] args) {
		//array [] com estrutura de repetição (for)
		int[] numeros = new int [10];
		int i;
		for( i = 0;i  < numeros.length; i++) {
			numeros[i] = Integer.parseInt(JOptionPane.showInputDialog("INFORME UM NÚMERO"));
		}
		i = 0;
		while (i<10) {
			JOptionPane.showMessageDialog(null, numeros[i]);
			i++;
		}
	}

}
