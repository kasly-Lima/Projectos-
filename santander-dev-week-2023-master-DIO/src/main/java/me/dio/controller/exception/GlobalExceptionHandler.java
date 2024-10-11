package me.dio.controller.exception;

// Importa as classes necessárias para o tratamento de exceções e para a construção de respostas HTTP
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import java.util.NoSuchElementException;

// Anotação que indica que esta classe é um manipulador global de exceções
@RestControllerAdvice
public class GlobalExceptionHandler {

    // Cria um logger para registrar mensagens de erro
    private final Logger logger  = LoggerFactory.getLogger(GlobalExceptionHandler.class);

    // Método para tratar exceções do tipo IllegalArgumentException
    @ExceptionHandler(IllegalArgumentException.class)
    public ResponseEntity<String> handleBusinessException(IllegalArgumentException businessException) {
        // Retorna uma resposta com a mensagem da exceção e status HTTP 422 (Unprocessable Entity)
        return new ResponseEntity<>(businessException.getMessage(), HttpStatus.UNPROCESSABLE_ENTITY);
    }

    // Método para tratar exceções do tipo NoSuchElementException
    @ExceptionHandler(NoSuchElementException.class)
    public ResponseEntity<String> handleNotFoundException(NoSuchElementException notFoundException) {
        // Retorna uma resposta com uma mensagem padrão e status HTTP 404 (Not Found)
        return new ResponseEntity<>("Resource ID not found.", HttpStatus.NOT_FOUND);
    }

    // Método para tratar qualquer outra exceção não esperada
    @ExceptionHandler(Throwable.class)
    public ResponseEntity<String> handleUnexpectedException(Throwable unexpectedException) {
        // Mensagem padrão para erros inesperados
        var message = "Unexpected server error, see the logs.";
        // Registra o erro nos logs para análise posterior
        logger.error(message, unexpectedException);
        // Retorna uma resposta com a mensagem padrão e status HTTP 500 (Internal Server Error)
        return new ResponseEntity<>(message, HttpStatus.INTERNAL_SERVER_ERROR);
    }
}

