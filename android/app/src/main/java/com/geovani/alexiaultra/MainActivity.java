package com.geovani.alexiaultra;

import android.app.Activity;
import android.graphics.Color;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class MainActivity extends Activity {

    private LinearLayout tela;
    private LinearLayout mensagens;
    private EditText campoMensagem;

    private final ExecutorService executor =
            Executors.newSingleThreadExecutor();

    private final List<JSONObject> historico =
            new ArrayList<>();

    private static final String API_URL =
            "https://ultra-ia-pro.onrender.com/api/chat";
    private static final String PONTE_API_URL =
        "https://ultra-ia-pro.onrender.com/api/ponte/processar";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        entrarEmTelaCheia();
        criarInterface();
    }

    private void entrarEmTelaCheia() {

        getWindow().getDecorView().setSystemUiVisibility(
                View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY
                        | View.SYSTEM_UI_FLAG_FULLSCREEN
                        | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
                        | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
                        | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
                        | View.SYSTEM_UI_FLAG_LAYOUT_STABLE
        );
    }

    private void criarInterface() {

        tela = new LinearLayout(this);
        tela.setOrientation(LinearLayout.VERTICAL);
        tela.setBackgroundColor(Color.rgb(8, 12, 20));

        // ============================================================
        // CABEÇALHO
        // ============================================================

        TextView titulo = new TextView(this);

        titulo.setText("🤖 Alex IA Ultra");
        titulo.setTextColor(Color.WHITE);
        titulo.setTextSize(22);
        titulo.setGravity(Gravity.CENTER);
        titulo.setPadding(20, 30, 20, 30);

        tela.addView(
                titulo,
                new LinearLayout.LayoutParams(
                        ViewGroup.LayoutParams.MATCH_PARENT,
                        ViewGroup.LayoutParams.WRAP_CONTENT
                )
        );

        // ============================================================
        // ÁREA DE MENSAGENS
        // ============================================================

        ScrollView scroll = new ScrollView(this);

        mensagens = new LinearLayout(this);
        mensagens.setOrientation(LinearLayout.VERTICAL);
        mensagens.setPadding(20, 20, 20, 20);

        TextView boasVindas = new TextView(this);

        boasVindas.setText(
                "Olá! Eu sou a Alex IA Ultra.\n\n"
                        + "Agora estou conectada ao meu cérebro de IA."
        );

        boasVindas.setTextColor(Color.WHITE);
        boasVindas.setTextSize(17);
        boasVindas.setPadding(25, 25, 25, 25);

        mensagens.addView(boasVindas);

        scroll.addView(mensagens);

        tela.addView(
                scroll,
                new LinearLayout.LayoutParams(
                        ViewGroup.LayoutParams.MATCH_PARENT,
                        0,
                        1
                )
        );

        // ============================================================
        // ÁREA DE DIGITAÇÃO
        // ============================================================

        LinearLayout entrada = new LinearLayout(this);
        entrada.setOrientation(LinearLayout.HORIZONTAL);
        entrada.setPadding(15, 15, 15, 15);

        campoMensagem = new EditText(this);

        campoMensagem.setHint("Digite uma mensagem...");
        campoMensagem.setHintTextColor(Color.LTGRAY);
        campoMensagem.setTextColor(Color.WHITE);
        campoMensagem.setTextSize(16);

        entrada.addView(
                campoMensagem,
                new LinearLayout.LayoutParams(
                        0,
                        ViewGroup.LayoutParams.WRAP_CONTENT,
                        1
                )
        );

        Button enviar = new Button(this);

        enviar.setText("Enviar");

        enviar.setOnClickListener(
                v -> enviarMensagem()
        );

        entrada.addView(
                enviar,
                new LinearLayout.LayoutParams(
                        ViewGroup.LayoutParams.WRAP_CONTENT,
                        ViewGroup.LayoutParams.WRAP_CONTENT
                )
        );

        tela.addView(
                entrada,
                new LinearLayout.LayoutParams(
                        ViewGroup.LayoutParams.MATCH_PARENT,
                        ViewGroup.LayoutParams.WRAP_CONTENT
                )
        );// ============================================================
          // ÁREA DA PONTE ALEX V2
          // ============================================================

          TextView tituloPonte = new TextView(this);

          tituloPonte.setText("🌉 Ponte Alex v2");
          tituloPonte.setTextColor(Color.WHITE);
          tituloPonte.setTextSize(19);
          tituloPonte.setPadding(20, 20, 20, 10);

          tela.addView(
                  tituloPonte,
                  new LinearLayout.LayoutParams(
                          ViewGroup.LayoutParams.MATCH_PARENT,
                          ViewGroup.LayoutParams.WRAP_CONTENT
                  )
          );

          EditText campoCodigo = new EditText(this);

          campoCodigo.setHint(
                  "Cole aqui o código do arquivo..."
          );

          campoCodigo.setHintTextColor(Color.LTGRAY);
          campoCodigo.setTextColor(Color.WHITE);
          campoCodigo.setTextSize(15);
          campoCodigo.setGravity(Gravity.TOP);
          campoCodigo.setMinLines(5);
          campoCodigo.setPadding(20, 20, 20, 20);

          tela.addView(
                  campoCodigo,
                  new LinearLayout.LayoutParams(
                          ViewGroup.LayoutParams.MATCH_PARENT,
                          300
                  )
          );

          EditText campoInstrucao = new EditText(this);

          campoInstrucao.setHint(
                  "O que a Ponte deve fazer?"
          );

          campoInstrucao.setHintTextColor(Color.LTGRAY);
          campoInstrucao.setTextColor(Color.WHITE);
          campoInstrucao.setTextSize(15);
          campoInstrucao.setPadding(20, 15, 20, 15);

          tela.addView(
                  campoInstrucao,
                  new LinearLayout.LayoutParams(
                          ViewGroup.LayoutParams.MATCH_PARENT,
                          ViewGroup.LayoutParams.WRAP_CONTENT
                  )
          );

          Button enviarPonte = new Button(this);

          enviarPonte.setText(
                  "🌉 Processar pela Ponte"
          );

          enviarPonte.setOnClickListener(
                  v -> processarPelaPonte(
                          campoCodigo.getText().toString(),
                          campoInstrucao.getText().toString()
                  )
          );

          tela.addView(
                  enviarPonte,
                  new LinearLayout.LayoutParams(
                          ViewGroup.LayoutParams.MATCH_PARENT,
                          ViewGroup.LayoutParams.WRAP_CONTENT
                  )
          );

        setContentView(tela);
    }

    // ============================================================
    // ENVIAR MENSAGEM PARA A API
    // ============================================================

    private void enviarMensagem() {

        String texto = campoMensagem
                .getText()
                .toString()
                .trim();

        if (texto.isEmpty()) {
            return;
        }

        adicionarMensagem("Você: " + texto);

        campoMensagem.setText("");

        adicionarMensagem("Alex: pensando...");

        executor.execute(() -> {

            try {

                JSONObject pedido = new JSONObject();

                pedido.put(
                        "pergunta",
                        texto
                );

                JSONArray arrayHistorico =
                        new JSONArray();

                for (JSONObject item : historico) {
                    arrayHistorico.put(item);
                }

                pedido.put(
                        "historico",
                        arrayHistorico
                );

                pedido.put(
                        "contexto_arquivo",
                        ""
                );

                pedido.put(
                        "nome_arquivo",
                        ""
                );

                URL url = new URL(API_URL);

                HttpURLConnection conexao =
                        (HttpURLConnection) url.openConnection();

                conexao.setRequestMethod("POST");
                conexao.setRequestProperty(
                        "Content-Type",
                        "application/json"
                );
                conexao.setRequestProperty(
                        "Accept",
                        "application/json"
                );

                conexao.setDoOutput(true);
                conexao.setConnectTimeout(30000);
                conexao.setReadTimeout(60000);

                byte[] dados =
                        pedido.toString()
                                .getBytes(StandardCharsets.UTF_8);

                try (OutputStream saida =
                             conexao.getOutputStream()) {

                    saida.write(dados);
                }

                int codigo =
                        conexao.getResponseCode();

                InputStream entradaResposta;

                if (codigo >= 200 && codigo < 300) {
                    entradaResposta =
                            conexao.getInputStream();
                } else {
                    entradaResposta =
                            conexao.getErrorStream();
                }

                String respostaTexto =
                        lerResposta(entradaResposta);

                conexao.disconnect();

                JSONObject resposta =
                        new JSONObject(respostaTexto);

                boolean sucesso =
                        resposta.optBoolean(
                                "success",
                                false
                        );

                String respostaAlex =
                        resposta.optString(
                                "resposta",
                                "Não consegui obter uma resposta."
                        );

                if (sucesso) {

                    JSONObject mensagemUsuario =
                            new JSONObject();

                    mensagemUsuario.put(
                            "role",
                            "user"
                    );

                    mensagemUsuario.put(
                            "content",
                            texto
                    );

                    JSONObject mensagemAlex =
                            new JSONObject();

                    mensagemAlex.put(
                            "role",
                            "model"
                    );

                    mensagemAlex.put(
                            "content",
                            respostaAlex
                    );

                    historico.add(
                            mensagemUsuario
                    );

                    historico.add(
                            mensagemAlex
                    );
                }

                runOnUiThread(() -> {

                    removerMensagemPensando();

                    if (sucesso) {

                        adicionarMensagem(
                                "Alex: " + respostaAlex
                        );

                    } else {

                        adicionarMensagem(
                                "Alex: " + respostaAlex
                        );
                    }
                });

            } catch (Exception erro) {

                runOnUiThread(() -> {

                    removerMensagemPensando();

                    adicionarMensagem(
                            "Alex: Não consegui conectar "
                                    + "ao servidor agora."
                    );
                });
            }
        });
    }

    // ============================================================
    // LER RESPOSTA DO SERVIDOR
    // ============================================================

    private String lerResposta(
            InputStream entrada
    ) throws Exception {

        if (entrada == null) {
            return "{\"success\":false,"
                    + "\"resposta\":\"Resposta vazia do servidor.\"}";
        }

        StringBuilder resultado =
                new StringBuilder();

        BufferedReader leitor =
                new BufferedReader(
                        new InputStreamReader(
                                entrada,
                                StandardCharsets.UTF_8
                        )
                );

        String linha;

        while ((linha = leitor.readLine()) != null) {
            resultado.append(linha);
        }

        leitor.close();

        return resultado.toString();
    }
    // ============================================================
    // PROCESSAR CÓDIGO PELA PONTE ALEX V2
    // ============================================================

    private void processarPelaPonte(
            String codigo,
            String instrucao
    ) {

        codigo = codigo.trim();
        instrucao = instrucao.trim();

        if (codigo.isEmpty()) {

            adicionarMensagem(
                    "Ponte: cole um código para processar."
            );

            return;
        }

        if (instrucao.isEmpty()) {

            adicionarMensagem(
                   "Ponte: informe o que deseja modificar."
            );

            return;
        }

        adicionarMensagem(
                "Você → Ponte: processando..."
        );

        final String codigoFinal = codigo;
        final String instrucaoFinal = instrucao;

        executor.execute(() -> {

            HttpURLConnection conexao = null;

            try {

                JSONObject pedido = new JSONObject();

                pedido.put(
                        "fileContent",
                        codigoFinal
                );

                pedido.put(
                       "instruction",
                        instrucaoFinal
                );

                pedido.put(
                        "filename",
                        "script_alex.py"
                );

                pedido.put(
                        "outputFilename",
                        JSONObject.NULL
                );

                pedido.put(
                        "searchTarget",
                        JSONObject.NULL
                );

                pedido.put(
                        "replaceWith",
                        JSONObject.NULL
                );

                URL url =
                        new URL(PONTE_API_URL);

                conexao =
                        (HttpURLConnection)
                                url.openConnection();

                conexao.setRequestMethod("POST");

                conexao.setRequestProperty(
                        "Content-Type",
                        "application/json"
                );

                conexao.setRequestProperty(
                        "Accept",
                        "application/json"
                );

                conexao.setDoOutput(true);

                conexao.setConnectTimeout(
                        30000
                );

                conexao.setReadTimeout(
                        90000
                );

                byte[] dados =
                        pedido.toString()
                                .getBytes(
                                        StandardCharsets.UTF_8
                                );

                try (
                        OutputStream saida =
                                conexao.getOutputStream()
                ) {

                    saida.write(dados);
                }

                int codigoHttp =
                        conexao.getResponseCode();

                InputStream entradaResposta;

                if (
                        codigoHttp >= 200
                                && codigoHttp < 300
                ) {

                    entradaResposta =
                            conexao.getInputStream();

                } else {

                    entradaResposta =
                            conexao.getErrorStream();
                }

                String respostaTexto =
                        lerResposta(
                                entradaResposta
                        );

                JSONObject resposta =
                        new JSONObject(
                                respostaTexto
                        );

                boolean sucesso =
                        resposta.optBoolean(
                                "success",
                                false
                        );

                if (sucesso) {

                    JSONObject arquivo =
                            resposta.optJSONObject(
                                    "processedFile"
                            );

                    String nomeArquivo =
                            arquivo != null
                                    ? arquivo.optString(
                                            "filename",
                                            ""
                                    )
                                    : "";

                    String download =
                            arquivo != null
                                    ? arquivo.optString(
                                            "downloadUrl",
                                            ""
                                    )
                                    : "";

                    String status =
                            resposta.optString(
                                    "status",
                                    "PROCESSADO"
                            );

                    runOnUiThread(() -> {

                        adicionarMensagem(
                                "Ponte: " + status
                                        + "\nArquivo processado: "
                                        + nomeArquivo
                                        + (
                                            download.isEmpty()
                                                ? ""
                                                : "\nDownload: "
                                                    + download
                                        )
                        );
                    });

                } else {

                    String erro =
                            resposta.optString(
                                    "error",
                                    resposta.optString(
                                            "resposta",
                                            "A Ponte não conseguiu processar."
                                    )
                            );

                    runOnUiThread(() -> {

                        adicionarMensagem(
                                "Ponte: " + erro
                        );
                    });
                }

            } catch (Exception erro) {

                runOnUiThread(() -> {

                    adicionarMensagem(
                            "Ponte: não foi possível "
                                    + "conectar ao servidor."
                    );
                });

            } finally {

                if (conexao != null) {
                    conexao.disconnect();
                }
            }
        });
    }

    // ============================================================
    // MENSAGEM "PENSANDO..."
    // ============================================================

    private void removerMensagemPensando() {

        int quantidade =
                mensagens.getChildCount();

        if (quantidade == 0) {
            return;
        }

        View ultima =
                mensagens.getChildAt(
                        quantidade - 1
                );

        if (ultima instanceof TextView) {

            TextView texto =
                    (TextView) ultima;

            String valor =
                    texto.getText().toString();

            if (valor.equals(
                    "Alex: pensando..."
            )) {

                mensagens.removeView(
                        ultima
                );
            }
        }
    }

    // ============================================================
    // ADICIONAR MENSAGEM NA TELA
    // ============================================================

    private void adicionarMensagem(
            String texto
    ) {

        TextView mensagem =
                new TextView(this);

        mensagem.setText(texto);
        mensagem.setTextColor(Color.WHITE);
        mensagem.setTextSize(16);
        mensagem.setPadding(
                20,
                15,
                20,
                15
        );

        mensagens.addView(mensagem);
    }

    @Override
    protected void onDestroy() {

        executor.shutdownNow();

        super.onDestroy();
    }

    @Override
    public void onBackPressed() {
        super.onBackPressed();
    }
}
