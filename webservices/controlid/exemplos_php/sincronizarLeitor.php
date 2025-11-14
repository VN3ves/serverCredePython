<?php
/**
 * Exemplo de uso do sincronizarLeitor.py via PHP
 * 
 * Este script força a sincronização de todas as imagens para um leitor específico.
 * Ignora o histórico e reenvia tudo para garantir 100% de sincronização.
 */

/**
 * Sincroniza todas as imagens para um leitor específico
 * 
 * @param int $leitorId ID do leitor
 * @return array Resultado da sincronização
 */
function sincronizarLeitor($leitorId) {
    $pythonScript = '/var/www/server/webservices/controlid/sincronizarLeitor.py';
    $pythonBin = '/usr/bin/python3';
    
    // Monta o comando
    $command = sprintf(
        '%s %s %d 2>&1',
        escapeshellcmd($pythonBin),
        escapeshellarg($pythonScript),
        intval($leitorId)
    );
    
    // Executa o comando
    exec($command, $output, $returnCode);
    
    // Pega a última linha (JSON de resultado)
    $outputString = implode("\n", $output);
    $lastLine = trim(end($output));
    
    // Tenta decodificar o JSON
    $resultado = json_decode($lastLine, true);
    
    if (json_last_error() === JSON_ERROR_NONE) {
        return [
            'sucesso' => $resultado['sucesso'] ?? false,
            'total_pessoas' => $resultado['total_pessoas'] ?? 0,
            'total_imagens_enviadas' => $resultado['total_imagens_enviadas'] ?? 0,
            'total_erros' => $resultado['total_erros'] ?? 0,
            'erros' => $resultado['erros'] ?? [],
            'mensagem' => $resultado['mensagem'] ?? '',
            'duracao_segundos' => $resultado['duracao_segundos'] ?? 0,
            'return_code' => $returnCode,
            'output_completo' => $outputString
        ];
    } else {
        return [
            'sucesso' => false,
            'mensagem' => 'Erro ao decodificar resposta do Python',
            'return_code' => $returnCode,
            'output_completo' => $outputString
        ];
    }
}

// ============================================
// EXEMPLOS DE USO
// ============================================

// Exemplo 1: Sincronizar leitor ID 5
$resultado = sincronizarLeitor(5);

if ($resultado['sucesso']) {
    echo "✓ Sincronização concluída com sucesso!\n";
    echo "  - Total de pessoas: {$resultado['total_pessoas']}\n";
    echo "  - Imagens enviadas: {$resultado['total_imagens_enviadas']}\n";
    echo "  - Duração: {$resultado['duracao_segundos']}s\n";
} else {
    echo "✗ Falha na sincronização\n";
    echo "  - Mensagem: {$resultado['mensagem']}\n";
    if (!empty($resultado['erros'])) {
        echo "  - Erros:\n";
        foreach ($resultado['erros'] as $erro) {
            echo "    • $erro\n";
        }
    }
}

// ============================================
// EXEMPLO 2: Integração com Laravel/CodeIgniter
// ============================================

/*
// Em um Controller Laravel:
public function sincronizarLeitor(Request $request)
{
    $leitorId = $request->input('leitor_id');
    
    // Validação
    $leitor = Leitor::find($leitorId);
    if (!$leitor) {
        return response()->json(['error' => 'Leitor não encontrado'], 404);
    }
    
    // Executa sincronização
    $resultado = sincronizarLeitor($leitorId);
    
    // Registra no log
    Log::info('Sincronização forçada', [
        'leitor_id' => $leitorId,
        'resultado' => $resultado
    ]);
    
    // Retorna resultado
    if ($resultado['sucesso']) {
        return response()->json([
            'message' => 'Sincronização concluída',
            'data' => $resultado
        ], 200);
    } else {
        return response()->json([
            'message' => 'Falha na sincronização',
            'error' => $resultado['mensagem'],
            'data' => $resultado
        ], 500);
    }
}
*/

// ============================================
// EXEMPLO 3: Sincronizar todos os leitores
// ============================================

/*
function sincronizarTodosLeitores($pdo)
{
    // Busca todos os leitores ativos
    $stmt = $pdo->query("
        SELECT id, nomeLeitor 
        FROM tblLeitor 
        WHERE status = 'T' AND configurado = 'T'
    ");
    
    $resultados = [];
    
    while ($leitor = $stmt->fetch(PDO::FETCH_ASSOC)) {
        echo "Sincronizando {$leitor['nomeLeitor']}...\n";
        
        $resultado = sincronizarLeitor($leitor['id']);
        $resultados[] = [
            'leitor_id' => $leitor['id'],
            'leitor_nome' => $leitor['nomeLeitor'],
            'resultado' => $resultado
        ];
        
        // Aguarda 2 segundos entre cada leitor
        sleep(2);
    }
    
    return $resultados;
}
*/

// ============================================
// EXEMPLO 4: API REST Endpoint
// ============================================

/*
// api/sincronizar-leitor.php

header('Content-Type: application/json');

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['error' => 'Method not allowed']);
    exit;
}

$input = json_decode(file_get_contents('php://input'), true);
$leitorId = $input['leitor_id'] ?? null;

if (!$leitorId) {
    http_response_code(400);
    echo json_encode(['error' => 'leitor_id é obrigatório']);
    exit;
}

$resultado = sincronizarLeitor($leitorId);

if ($resultado['sucesso']) {
    http_response_code(200);
} else {
    http_response_code(500);
}

echo json_encode($resultado);
*/

