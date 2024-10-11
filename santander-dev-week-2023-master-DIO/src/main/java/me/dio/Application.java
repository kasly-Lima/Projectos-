package me.dio;

// Importa as classes necessárias para configuração do OpenAPI e o Spring Boot
import io.swagger.v3.oas.annotations.OpenAPIDefinition;
import io.swagger.v3.oas.annotations.servers.Server;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

// Anotação que define a configuração do OpenAPI para a aplicação
@OpenAPIDefinition(servers = { @Server(url = "/", description = "Default Server URL")})
// Anotação que indica que esta classe é a configuração principal do Spring Boot
@SpringBootApplication
public class Application {

	// Método principal que inicia a aplicação Spring Boot
	public static void main(String[] args) {
		// Executa a aplicação Spring
		SpringApplication.run(Application.class, args);
	}

}
