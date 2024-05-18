/**
 * 
 */
package exercicioSenai;

import java.util.Locale;
import java.util.Scanner;

public class Exercicio2 {

	
	public static void main(String[] args) {
		
//		o LOCALE é para localizar o arquivo com a liguagem para inserir  
		Locale.setDefault(Locale.US);
		
//		utilizando a classe Scanner para solicitar informação do usuario (System.in)
		Scanner sc = new Scanner(System.in);
		
		
//		declarando as variaveis (o comando "final" antes do double obriga o resultado ser sempre o informado, não podendo mudar o valor da variavel)
		final double pi = 3.1415;
		double raio, area;
		
//		pedindo para o usuario informar os dados do raio  
		System.out.print("Entre com o raio do circulo");
		raio = sc.nextDouble();
		
//		conta 
		area = pi * (raio * raio);
		
//		imprimindo com formatação para não concatenar usando %.2f 
		System.out.printf(" A área do circulo com o raio %.2f é igua a %.2f: ", raio,area);
		
		
		
		
		
		
//		encer o escanner
		sc.close();

	}

}
