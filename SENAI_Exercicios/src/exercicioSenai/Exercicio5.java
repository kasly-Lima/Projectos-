/**
 * 
 */
package exercicioSenai;

import java.time.LocalDate;
import java.util.Scanner;

public class Exercicio5 {

	
	public static void main(String[] args) {

//		importando o Scanner
		Scanner sc = new Scanner(System.in);
		
//		faz com que o sistema mantenha a data atualizada
		LocalDate data = LocalDate.now();
		
//		declarando as variaveis
		int anonascimento, anoatual, idade;
		
		System.out.print("Digite o ano que você nasceu: ");
		anonascimento = sc.nextInt();
		
		anoatual = LocalDate.now().getYear();
		
		idade = anoatual - anonascimento;
		
		System.out.printf("Com a data atual %s você tem %d anos", data, idade);
		
		sc.close();

	}

}
