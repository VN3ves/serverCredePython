<?php
/**
 * Exemplo de uso do processarJobsSync.py via PHP
 * 
 * Sistema de fila de jobs similar ao Laravel Queue.
 * Quando uma foto é cadastrada, cria-se um job que será processado pelo Python.
 */

/**
 * Cria um novo job de sincronização de imagem
 * 
 * @param PDO $pdo Conexão com o banco
 * @param int $eventoId ID do evento
 * @param int $pessoaId ID da pessoa
 * @param int $arquivoId ID do arquivo/foto
 * @param int $prioridade Prioridade (1=Máxima, 10=Mínima)
 * @return int|false ID do job criado ou false em caso de erro
 */
function criarJobSyncImagem($pdo, $eventoId, $pessoaId, $arquivoId, $prioridade = 5) {
    try {
        $stmt = $pdo->prepare("
            INSERT INTO tblJobSync (
                idEvento, 
                idPessoa, 
                idArquivo, 
                tipoJob, 
                prioridade,
                status,
                dataAgendamento
            ) VALUES (
                :evento_id,
                :pessoa_id,
                :arquivo_id,
                'SYNC_IMAGEM',
                :prioridade,
                'PENDENTE',
                NOW()
            )
        ");
        
        $stmt->execute([
            ':evento_id' => $eventoId,
            ':pessoa_id' => $pessoaId,
            ':arquivo_id' => $arquivoId,
            ':prioridade' => $prioridade
        ]);
        
        return $pdo->lastInsertId();
        
    } catch (PDOException $e) {
        error_log("Erro ao criar job: " . $e->getMessage());
        return false;
    }
}

/**
 * Processa jobs pendentes
 * 
 * @param int $limit Número máximo de jobs a processar
 * @return array Resultado do processamento
 */
function processarJobs($limit = 10) {
    $pythonScript = '/var/www/server/webservices/controlid/processarJobsSync.py';
    $pythonBin = '/usr/bin/python3';
    
    // Monta o comando
    $command = sprintf(
        '%s %s --limit %d 2>&1',
        escapeshellcmd($pythonBin),
        escapeshellarg($pythonScript),
        intval($limit)
    );
    
    // Executa o comando
    exec($command, $output, $returnCode);
    
    // Pega a última linha (JSON de resultado)
    $lastLine = trim(end($output));
    
    // Tenta decodificar o JSON
    $resultado = json_decode($lastLine, true);
    
    if (json_last_error() === JSON_ERROR_NONE) {
        return [
            'sucesso' => $resultado['sucesso'] ?? false,
            'jobs_processados' => $resultado['jobs_processados'] ?? 0,
            'sucessos' => $resultado['sucessos'] ?? 0,
            'falhas' => $resultado['falhas'] ?? 0,
            'mensagem' => $resultado['mensagem'] ?? '',
            'duracao_segundos' => $resultado['duracao_segundos'] ?? 0,
            'return_code' => $returnCode
        ];
    } else {
        return [
            'sucesso' => false,
            'mensagem' => 'Erro ao decodificar resposta',
            'return_code' => $returnCode,
            'output' => implode("\n", $output)
        ];
    }
}

/**
 * Processa um job específico
 * 
 * @param int $jobId ID do job
 * @return array Resultado do processamento
 */
function processarJobEspecifico($jobId) {
    $pythonScript = '/var/www/server/webservices/controlid/processarJobsSync.py';
    $pythonBin = '/usr/bin/python3';
    
    $command = sprintf(
        '%s %s --job-id %d 2>&1',
        escapeshellcmd($pythonBin),
        escapeshellarg($pythonScript),
        intval($jobId)
    );
    
    exec($command, $output, $returnCode);
    
    $lastLine = trim(end($output));
    $resultado = json_decode($lastLine, true);
    
    if (json_last_error() === JSON_ERROR_NONE) {
        return $resultado;
    } else {
        return [
            'sucesso' => false,
            'mensagem' => 'Erro ao processar job',
            'output' => implode("\n", $output)
        ];
    }
}

// ============================================
// EXEMPLO 1: Criar job ao cadastrar foto
// ============================================

/*
// Quando uma foto é cadastrada/atualizada:

$pdo = new PDO('mysql:host=localhost;dbname=tcc_crede', 'crede', 'crede@123');

// Dados da foto cadastrada
$eventoId = 1;
$pessoaId = 123;
$arquivoId = 456; // ID do arquivo recém criado

// Cria o job
$jobId = criarJobSyncImagem($pdo, $eventoId, $pessoaId, $arquivoId, 1); // Prioridade 1 (máxima)

if ($jobId) {
    echo "✓ Job $jobId criado com sucesso!\n";
    
    // OPÇÃO 1: Processar imediatamente (síncrono - pode demorar)
    // $resultado = processarJobEspecifico($jobId);
    
    // OPÇÃO 2: Processar em background (recomendado)
    shell_exec("php processar-jobs-background.php > /dev/null 2>&1 &");
    
    echo "  Job será processado em breve\n";
} else {
    echo "✗ Erro ao criar job\n";
}
*/

// ============================================
// EXEMPLO 2: Integração com Laravel
// ============================================

/*
// Em um Controller ou Service Laravel:

use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Log;

class FotoController extends Controller
{
    public function store(Request $request)
    {
        // Salva a foto
        $arquivo = Arquivo::create([
            'idReferencia' => $request->pessoa_id,
            'tipoReferencia' => 'PESSOA',
            'tipoArquivo' => 'AVATAR',
            'pathNuvem' => $request->imagem_base64
        ]);
        
        // Cria job para sincronizar
        $jobId = DB::table('tblJobSync')->insertGetId([
            'idEvento' => $request->evento_id,
            'idPessoa' => $request->pessoa_id,
            'idArquivo' => $arquivo->id,
            'tipoJob' => 'SYNC_IMAGEM',
            'prioridade' => 1,
            'status' => 'PENDENTE',
            'dataAgendamento' => now()
        ]);
        
        // Dispara processamento em background
        dispatch(function() use ($jobId) {
            $output = shell_exec(
                "python3 /var/www/server/webservices/controlid/processarJobsSync.py --job-id $jobId 2>&1"
            );
            Log::info("Job $jobId processado", ['output' => $output]);
        })->afterResponse();
        
        return response()->json([
            'message' => 'Foto cadastrada',
            'arquivo_id' => $arquivo->id,
            'job_id' => $jobId
        ], 201);
    }
    
    public function processarJobs()
    {
        $resultado = processarJobs(20); // Processa até 20 jobs
        
        return response()->json($resultado);
    }
}
*/

// ============================================
// EXEMPLO 3: Cron job para processar fila
// ============================================

/*
// Criar arquivo: /var/www/server/cron/processar-jobs.php

<?php
require_once __DIR__ . '/../webservices/controlid/exemplos_php/processarJobsSync.php';

$resultado = processarJobs(50); // Processa até 50 jobs por execução

echo "[" . date('Y-m-d H:i:s') . "] ";
if ($resultado['sucesso']) {
    echo "✓ Processados: {$resultado['jobs_processados']} | ";
    echo "Sucessos: {$resultado['sucessos']} | ";
    echo "Falhas: {$resultado['falhas']}\n";
} else {
    echo "✗ Erro: {$resultado['mensagem']}\n";
}

// Adicionar ao crontab para rodar a cada minuto:
// * * * * * /usr/bin/php /var/www/server/cron/processar-jobs.php >> /var/www/logs/cron-jobs.log 2>&1
?>
*/

// ============================================
// EXEMPLO 4: API REST para gerenciar jobs
// ============================================

/*
// api/jobs.php

header('Content-Type: application/json');

$pdo = new PDO('mysql:host=localhost;dbname=tcc_crede', 'crede', 'crede@123');
$method = $_SERVER['REQUEST_METHOD'];
$path = $_GET['action'] ?? '';

switch ($method . ':' . $path) {
    case 'POST:criar':
        // Criar novo job
        $input = json_decode(file_get_contents('php://input'), true);
        
        $jobId = criarJobSyncImagem(
            $pdo,
            $input['evento_id'],
            $input['pessoa_id'],
            $input['arquivo_id'],
            $input['prioridade'] ?? 5
        );
        
        if ($jobId) {
            // Dispara processamento
            shell_exec("php processar-jobs-background.php > /dev/null 2>&1 &");
            
            http_response_code(201);
            echo json_encode([
                'success' => true,
                'job_id' => $jobId,
                'message' => 'Job criado e enviado para processamento'
            ]);
        } else {
            http_response_code(500);
            echo json_encode(['error' => 'Erro ao criar job']);
        }
        break;
        
    case 'POST:processar':
        // Processar jobs pendentes
        $resultado = processarJobs(10);
        
        echo json_encode($resultado);
        break;
        
    case 'GET:status':
        // Verificar status dos jobs
        $stmt = $pdo->query("
            SELECT 
                status,
                COUNT(*) as total
            FROM tblJobSync
            GROUP BY status
        ");
        
        $stats = $stmt->fetchAll(PDO::FETCH_KEY_PAIR);
        
        echo json_encode([
            'pendentes' => $stats['PENDENTE'] ?? 0,
            'processando' => $stats['PROCESSANDO'] ?? 0,
            'concluidos' => $stats['CONCLUIDO'] ?? 0,
            'falhas' => $stats['FALHA'] ?? 0
        ]);
        break;
        
    case 'GET:listar':
        // Listar jobs
        $status = $_GET['status'] ?? 'PENDENTE';
        $limit = intval($_GET['limit'] ?? 10);
        
        $stmt = $pdo->prepare("
            SELECT 
                j.*,
                p.nome as pessoa_nome
            FROM tblJobSync j
            LEFT JOIN tblPessoa p ON p.id = j.idPessoa
            WHERE j.status = :status
            ORDER BY j.prioridade ASC, j.dataAgendamento DESC
            LIMIT :limit
        ");
        
        $stmt->bindValue(':status', $status);
        $stmt->bindValue(':limit', $limit, PDO::PARAM_INT);
        $stmt->execute();
        
        $jobs = $stmt->fetchAll(PDO::FETCH_ASSOC);
        
        echo json_encode([
            'total' => count($jobs),
            'jobs' => $jobs
        ]);
        break;
        
    default:
        http_response_code(404);
        echo json_encode(['error' => 'Endpoint não encontrado']);
}
*/

// ============================================
// EXEMPLO 5: Script de background
// ============================================

/*
// Criar arquivo: processar-jobs-background.php

<?php
// Este script é executado em background para processar jobs

set_time_limit(300); // 5 minutos
ignore_user_abort(true);

require_once __DIR__ . '/processarJobsSync.php';

// Processa jobs em lote
$resultado = processarJobs(20);

// Log do resultado
$logFile = '/var/www/logs/jobs-background.log';
$logMessage = sprintf(
    "[%s] Processados: %d | Sucessos: %d | Falhas: %d\n",
    date('Y-m-d H:i:s'),
    $resultado['jobs_processados'] ?? 0,
    $resultado['sucessos'] ?? 0,
    $resultado['falhas'] ?? 0
);

file_put_contents($logFile, $logMessage, FILE_APPEND);
?>
*/

// ============================================
// TESTE RÁPIDO
// ============================================

// Descomente para testar:
/*
echo "=== Teste de Processamento de Jobs ===\n\n";

$resultado = processarJobs(5);

echo "Sucesso: " . ($resultado['sucesso'] ? 'Sim' : 'Não') . "\n";
echo "Jobs processados: {$resultado['jobs_processados']}\n";
echo "Sucessos: {$resultado['sucessos']}\n";
echo "Falhas: {$resultado['falhas']}\n";
echo "Duração: {$resultado['duracao_segundos']}s\n";

if (isset($resultado['mensagem'])) {
    echo "Mensagem: {$resultado['mensagem']}\n";
}
*/

