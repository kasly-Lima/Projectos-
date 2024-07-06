/**
 * 
 */
package estruturadeRepeticao;

/**
 * 
 */
public class EstruturasDeRepeticaoFOR {

	/**
	 * @param args
	 */
	public static void main(String[] args) {
		
		int y = 0;
		
		
		for (int i = 0; i<10; i++) {
			
			y = y * i -1;
			
			if(y == -16) {
				continue;
			}
			
			System.out.println(y);
		}

	}

}
