package me.dio.controller;

// Importa as classes necessárias para o funcionamento do controlador
import me.dio.domain.model.User;
import me.dio.service.UserService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.support.ServletUriComponentsBuilder;

import java.net.URI;

// Anotação que indica que esta classe é um controlador REST
@RestController
@RequestMapping("/users") // Mapeia as requisições para a URL "/users"
public class UserController {

    private final UserService userService; // Serviço para manipulação de usuários

    // Construtor que recebe o UserService como dependência
    public UserController(UserService userService) {
        this.userService = userService; // Inicializa o serviço de usuários
    }

    // Método para buscar um usuário pelo ID
    @GetMapping("/{id}") // Mapeia requisições GET para "/users/{id}"
    public ResponseEntity<User> findById(@PathVariable Long id) {
        var user = userService.findById(id); // Busca o usuário no serviço
        return ResponseEntity.ok(user); // Retorna o usuário encontrado com status 200 (OK)
    }

    // Método para criar um novo usuário
    @PostMapping // Mapeia requisições POST para "/users"
    public ResponseEntity<User> create(@RequestBody User userToCreate) {
        var userCreated = userService.create(userToCreate); // Cria o usuário no serviço
        // Constrói a URI do novo recurso utilizando o ID do usuário criado
        URI location = ServletUriComponentsBuilder.fromCurrentRequest()
                .path("/{id}") // Adiciona o caminho do ID na URI
                .buildAndExpand(userCreated.getId()) // Substitui o ID na URI
                .toUri(); // Converte para um objeto URI
        // Retorna a resposta com status 201 (Created) e o novo usuário no corpo
        return ResponseEntity.created(location).body(userCreated);
    }
}
