
package introducao;

import java.util.InputMismatchException;
import java.util.Scanner;

public class Exercicio9 {

    public static void main(String[] args) {
        // Cria um objeto Scanner para ler a entrada do usuário
        Scanner sc = new Scanner(System.in);

        try {
            // Lê o número inserido pelo usuário
            System.out.print("Digite o dia da semana de hoje: ");
            int diaNumero = sc.nextInt();

            // Declara uma variável para armazenar o nome do dia da semana
            String diaSemana;

            // Usando a estrutura switch para associar o número ao dia da semana correspondente
            switch (diaNumero) {
                case 1:
                    diaSemana = "Domingo";
                    break;
                case 2:
                    diaSemana = "Segunda-feira";
                    break;
                case 3:
                    diaSemana = "Terça-feira";
                    break;
                case 4:
                    diaSemana = "Quarta-feira";
                    break;
                case 5:
                    diaSemana = "Quinta-feira";
                    break;
                case 6:
                    diaSemana = "Sexta-feira";
                    break;
                case 7:
                    diaSemana = "Sábado";
                    break;
                default:
                    diaSemana = "Inválido"; // Mensagem para números fora do intervalo 1-7
            }

            // Exibe o dia da semana correspondente
            System.out.printf("Hoje é %s, BOA SEMANA%n", diaSemana);
            System.out.println("Ufa, estamos no fim\n");
        } catch (InputMismatchException e) {
            System.out.println("Erro: Por favor, insira um número inteiro válido.");
        } finally {
            // Fecha o objeto Scanner para liberar os recursos
            sc.close();
        }
    }
}
