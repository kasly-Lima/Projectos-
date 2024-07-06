/**
 * 
 */
package estruturadeRepeticao;

import java.util.Scanner;

/**
 * 
 */
public class FuncaoWhile {

	
	public static void main(String[] args) {
//		metodo para ler a linha
		Scanner sc = new Scanner(System.in);
		
//		estrutura de repetição
		while (true) {
			
			System.out.print("Digite seu Nome");
			String nome = sc.nextLine();
			
//			toLowerCase() é usado para que o usuario escreva errado e o sistema corrija 
			if(nome.toLowerCase().equals("Sair")) {
				break;
			}
//			usando (%s) para concatenar o nome declarado na variavel
			System.out.printf("Seja bem-vindo %s fico feliz por ter voce aqui\n", nome);
			
		}
		
		sc.close();
	}

}
