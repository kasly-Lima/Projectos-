/**
 * 
 */
package introducao;

import java.util.Scanner;

public class Exercicio8 {

	
	public static void main(String[] args) {
		// Cria um objeto Scanner para ler a entrada do usuário
        Scanner sc = new Scanner(System.in);
		
        double conta = 79.30;
        int minutos; 
        
        
        System.out.print("Digite quantos minutos você utilizou: ");
        minutos = sc.nextInt();
        
        if (minutos > 100) {
        	conta += (minutos - 100) * 2.30;
        	
        }
		
        System.out.printf("Total da conta: R$%.2f", conta);
        
        sc.close();
    }
}
