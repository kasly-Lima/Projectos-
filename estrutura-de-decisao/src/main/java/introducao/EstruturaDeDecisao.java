/**
 * 
 */
package introducao;

public class EstruturaDeDecisao {


	public static void main(String[] args) {
		//declarando as variaveis
		double n1, n2, n3, media;
		
		n1 = 8;
		n2 = 8;
		n3 = 8;
		media = (n1 + n2 + n3) / 3.0 ;
		
//		if= se
		if ( media > 7.0 ) {
			System.out.printf("Sua media foi %.1f e voce foi Aprovado%n", media);
//		(else if) é senão si 
//		essas duas barras (||) siguinfica ou
//		e usando o (&&) significa (E), pode usar dependendo da resposta que voce queira passar	
		} else if (media > 5.0 || media < 7.0 ) {
			System.out.printf("Sua media foi %.1f e voce esta de Recuperação%n", media);
//			else = se não
		}else {
			System.out.printf("Sua media foi %.1f e voce foi Reprovado\n", media);
		}
		
		System.out.print("Obrigado por tirar a media conosco!");
		
	}

}
