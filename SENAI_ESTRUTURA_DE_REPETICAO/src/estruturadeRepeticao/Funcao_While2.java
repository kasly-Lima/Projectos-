/**
 * 
 */
package estruturadeRepeticao;

import java.util.Scanner;

/**
 * 
 */
public class Funcao_While2 {

	/**
	 * @param args
	 */
	public static void main(String[] args) {
		Scanner sc = new Scanner(System.in);
		
		String nome;
		
		do {
			System.out.print("Digite seu Nome");
			nome = sc.nextLine().toLowerCase();
			System.out.printf("Seja bem vindo %s fico muito feliz por ter você aqui\n" ,nome);
			
		}while (!nome.equals("Sair"));
		
		
		
		
		
		
		
		
		sc.close();

	}

}
