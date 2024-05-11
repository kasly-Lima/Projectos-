/**
 * 
 */
package br.com.produtos;

/**
 * 
 */
public class Produto {
	private int id;
	private String nome;
	private double valor;
	public int getId() {
		return id;
	}
	public void setId(int id) {
		this.id = id;
	}
	public String getNome() {
		return nome;
	}
	public void setNome(String nome) {
		this.nome = nome;
	}
	public double getValor() {
		return valor;
	}
	public void setValor(double valor) {
		this.valor = valor;
	}
	public Produto(int id, String nome, double valor) {
		super();
		this.id = id;
		this.nome = nome;
		this.valor = valor;
	}
	
	@Override
	public String toString() {
		//String linha = "\n" + this.getId() + "" + this.getNome() + "R$" + this.getValor();
		//return linha;
		String linha = String.format("%d %s R$ %2.f", this.getId(), this.getNome(), this.getValor());
		return linha;
	}
	
}
