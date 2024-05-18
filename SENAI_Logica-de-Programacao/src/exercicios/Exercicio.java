/**
 * 
 */
package exercicios;


public class Exercicio {


	public static void main(String[] args) {
		//declarando as variaveis
		String gameRPG, gameIndie;
		int age, code;
		char gender;
		double princeRPG, princieIndie, media;
		
		//declarou o valor e nomes das variaveis
		gameRPG = "Hogwarts Legacy";
		princeRPG= 107.80;
		//declarou o valor e nomes das variaveis
		gameIndie = "Hallow Knight";
		princieIndie = 49.99;
		
		//declarou o valor das variaveis
		age = 35;
		code = 2367;
		gender = 'M';
		
		media = (princeRPG + princieIndie) / 2;
				
		System.out.println("produtos:");
		System.out.println(gameRPG +" , está custando R$" + princeRPG);
		System.out.println(gameIndie + ", está custando R$" + princieIndie);
		
		System.out.printf("O comprador tinha %d anos, código %d e genero: %s%n" ,age, code, gender);
		
		System.out.printf("A média de preço dos produtos é igual a %.2f", media);
		 
		
	}

}
