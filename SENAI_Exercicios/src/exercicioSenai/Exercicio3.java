/**
 * 
 */
package exercicioSenai;

import java.util.Locale;
import java.util.Scanner;


public class Exercicio3 {

	
	public static void main(String[] args) {

//		o LOCALE é para localizar o arquivo com a liguagem para inserir  
		Locale.setDefault(Locale.US);
//		importando o Scanner
		Scanner sc = new Scanner(System.in);
		
//		declarando as variaveis
		double celsius, fahrenheit, kelvin, reaumur, rankine,rankine2;
//		solicita ao usuario para informar a temperatura 
		System.out.print("Informe a temperatura");
		celsius = sc.nextDouble();
		
		fahrenheit = celsius * 1.8 + 32 ;
		kelvin = celsius + 273.15;
		reaumur = celsius / 1.25;
		rankine = celsius * 1.8 + 491.67;
		rankine2 = (celsius + 273.15) * 9/5;
		
		
		System.out.printf("A temperatura %.1f° em fahrenheit: %.1f° %n", celsius, fahrenheit);
		System.out.printf("A temperatura %.1f° em kelvin: %.1f° %n", celsius, kelvin);
		System.out.printf("A temperatura %.1f° em reaumur: %.1f° %n", celsius, reaumur);
		System.out.printf("A temperatura %.1f° em rankine: %.1f° %n", celsius, rankine);
		System.out.printf("A temperatura %.1f° em rankine (2° formula): %.1f° %n", celsius, rankine2);
		
//		fecha o scanner
		sc.close();

	}

}
