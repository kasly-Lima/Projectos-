/**
 * 
 */
package arrayObjeto;

import javax.swing.JOptionPane;

import br.com.escola.Aluno;

/**
 * 
 */
public class ArrayObjeto {

	/**
	 * @param args
	 */
	public static void main(String[] args) {
		Aluno [] boletim = new Aluno [3];
		//declarando as variaveis
		int i;
		for(i = 0;i < boletim.length; i++ ) {
		int ra = Integer.parseInt(JOptionPane.showInputDialog("INFORME O RA"));
		String nome = JOptionPane.showInputDialog("INFORME O NOME");		
		float a1 = Float.parseFloat(JOptionPane.showInputDialog("INFORME A A1"));
		float a2 = Float.parseFloat(JOptionPane.showInputDialog("INFORME A A2"));
		//instanciando Aluno (apertar [Ctrl]+[ESPAÇO] depois que escrever new
		Aluno aluno = new Aluno(ra, nome, a1, a2);
		aluno.calcMedia();
		boletim[i] = aluno;			
	}
	
	StringBuilder sb = new StringBuilder();
	i = 0;
	while(1 < boletim.length) {
		sb.append(boletim[i].toString());
		i++;
	}
	
	JOptionPane.showMessageDialog(null, sb.toString());

	}
}