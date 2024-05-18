/**
 * 
 */
package exercicioSenai;

import java.util.Locale;
import java.util.Scanner;

/**
 * 
 */
public class Exercicio4 {
 
	
	public static void main(String[] args) {
//		o LOCALE é para localizar o arquivo com a liguagem para inserir  
		Locale.setDefault(Locale.US);
//		importando o Scanner
		Scanner sc = new Scanner(System.in);
		
		final double aluguelcobrado, kmcobrado;
		double diascomocarro, kmrodados, aluguelapagar;
		
		aluguelcobrado =86.75 ;
		kmcobrado = 1.23;
		
		
		System.out.println("Digite quantos dias voco ficou com o carro");
		diascomocarro = sc.nextDouble();
		
		System.out.println("Digite quantos km voc~e rodou com o carro");
		kmrodados = sc.nextDouble();
		
		aluguelapagar = (diascomocarro * aluguelcobrado) + (kmrodados * kmcobrado);
		System.out.printf("Você ira pagar para a empresa R$%2.f pelo aluguel do carro",aluguelapagar);
		
		sc.close();
	}

}
