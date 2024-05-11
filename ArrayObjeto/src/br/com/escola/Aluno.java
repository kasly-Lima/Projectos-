/**
 * 
 */
package br.com.escola;

/**
 * 
 */
public class Aluno {
	private int ra;
	private String nome;
	private float a1;
	private float a2;
	private float media;
	public int getRa() {
		return ra;
	//metodo getter e setter com o botão direito do mouse e clicar em getter e setter
	}
	public void setRa(int ra) {
		this.ra = ra;
	}
	public String getNome() {
		return nome;
	}
	public void setNome(String nome) {
		this.nome = nome;
	}
	public float getA1() {
		return a1;
	}
	public void setA1(float a1) {
		this.a1 = a1;
	}
	public float getA2() {
		return a2;
	}
	public void setA2(float a2) {
		this.a2 = a2;
	}
	public float getMedia() {
		return media;
	}
	public void setMedia(float media) {
		this.media = media;
	}
	
	public void calcMedia() {
		this.media = (this.getA1() + this.getA2()) / 2;
	}
	// esse é o constructor, apertar com o direito do mouse e clicar em source depois constructor using fields
	public Aluno(int ra, String nome, float a1, float a2) {
		super();
		this.ra = ra;
		this.nome = nome;
		this.a1 = a1;
		this.a2 = a2;
	}
	
	//escrever toString aperta [Ctrl]+[ESPAÇO] e depois [enter] para sobrescrever o metodo toString   
	@Override
	public String toString() {
		String linha = String.format("\nRa: %d Nome: %s A1: %.2f A2: %.2f Media: %.2f", this.getRa(), this.getNome() , this.getA1(), this.getA2(), this.getMedia());
		return super.toString();
	}
	
}
