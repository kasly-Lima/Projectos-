/**
 * 
 */
package introducao;

public class Exercicio10 {


	public static void main(String[] args) {
		 // Cria um objeto Scanner para ler a entrada do usuário
        Scanner scanner = new Scanner(System.in);

        // Lê o peso do usuário
        System.out.print("Enter your weight in kg: ");
        double weight = scanner.nextDouble();

        // Lê a altura do usuário
        System.out.print("Enter your height in meters: ");
        double height = scanner.nextDouble();

        // Calcula o IMC
        double imc = weight / (height * height);

        // Declara uma variável para armazenar a classificação do IMC
        String classification;

        // Determina a classificação do IMC com base no valor calculado
        if (imc < 18.5) {
            classification = "Magreza";
        } else if (imc >= 18.5 && imc <= 24.9) {
            classification = "Normal";
        } else if (imc >= 25 && imc <= 29.9) {
            classification = "Sobrepeso";
        } else if (imc >= 30 && imc <= 34.9) {
            classification = "Obesidade Grau 1";
        } else if (imc >= 35 && imc <= 39.9) {
            classification = "Obesidade Grau 2";
        } else {
            classification = "Obesidade Grau 3";
        }

        // Exibe o valor do IMC e a classificação correspondente
        System.out.printf("Your IMC is: %.2f\n", imc);
        System.out.println("IMC Classification: " + classification);

        // Fecha o objeto Scanner para liberar os recursos
        scanner.close();
    }
}