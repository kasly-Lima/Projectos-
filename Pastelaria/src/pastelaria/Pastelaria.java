/**
 * 
 */
package pastelaria;

import java.util.ArrayList;
import java.util.List;

import javax.swing.JOptionPane;

import br.com.produtos.Produto;

/**
 * 
 */
public class Pastelaria {

	/**
	 * @param args
	 */
	public static void main(String[] args) {
		List<Produto> lstProduto = new ArrayList<>();
		
		Produto produto = null;
		
		StringBuilder sb = new StringBuilder();
		sb.append("<<<< MENU >>>>\n");
		sb.append("1 - Cadastar Produto\n");
		sb.append("2 - listar Produto\n");
		sb.append("0 - Sair\n");
		int op = -1;
		while(op != 0) {
			op =Integer.parseInt(JOptionPane.showInputDialog(sb.toString()));
			switch (op) {
			case 1:
				int id = Integer.parseInt(JOptionPane.showInputDialog("Informe o ID"));
				String  nome = JOptionPane.showInputDialog("Informe o Nome");
				double  valor = Double.parseDouble(JOptionPane.showInputDialog("Informe o Valor"));
				
				Produto prod = new Produto (id, nome, valor);
				lstProduto.add(prod);
			
			break;
			case 2:
				int i;
				StringBuilder sb1 = new StringBuilder();
				/*for(i = 0;i < lstProduto.size(); i++) {
					sb1.append(lstProduto.get(i).toString());
				}*/
				double total = 0.0;
				for(Produto prod1: lstProduto) {
					sb1.append(prod1.toString());
					total = total + prod1.getValor();
				}
				sb1.append("------------------------------------------------------");
				sb1.append(String.format("\n     R$ %2.f", total));
				JOptionPane.showMessageDialog(null, sb1.toString());
				
			break;
			default:
				JOptionPane.showMessageDialog(null, "Operação INVALIDA");
			break;
			}
		
		}

	}
}