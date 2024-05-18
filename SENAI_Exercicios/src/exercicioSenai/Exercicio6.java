/**
 * 
 */
package exercicioSenai;

import java.util.Random;
import java.util.Scanner;

public class Exercicio6 {

	
	public static void main(String[] args) {
		
		Random rd = new Random();
		Scanner sc = new Scanner(System.in);
		
		String nome, curso, RA;
		byte idade;
		char genero;
		
		System.out.print("Digite o sue nome para cadastro");
		nome = sc.nextLine();
		
		System.out.print("Digite sua idade");
		idade = sc.nextByte();
		sc.nextLine();
		
		System.out.print("Digite o seu genero");
		String texto = sc.nextLine();
		genero = texto.toUpperCase().charAt(0);
		
		System.out.print("Digite o seu curso");
		curso = sc.nextLine();
		
//		Utilizando o método charAt
//		RA = nome.charAt(0) + String.valueof(rd.nextInt(100));
		
//		utilizando o metodo subString
		RA = nome.substring(0,1) + rd.nextInt(100);
		
		System.out.printf("Seu nome é %s e ele possui %s letras, sua idade é %d seu genero é %s " + "%nVocê se inscreveu no curso de %s com o RA %s",nome.toUpperCase(), nome.length(), idade, genero, curso.toLowerCase(), RA);
		
		sc.close();
	}

}
