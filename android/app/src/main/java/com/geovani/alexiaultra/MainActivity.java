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

public class MainActivity extends Activity {

    private LinearLayout tela;
    private LinearLayout mensagens;
    private EditText campoMensagem;

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
                + "A minha nova interface está funcionando."
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
        );

        setContentView(tela);
    }

    private void enviarMensagem() {

        String texto = campoMensagem
                .getText()
                .toString()
                .trim();

        if (texto.isEmpty()) {
            return;
        }

        adicionarMensagem(
                "Você: " + texto
        );

        campoMensagem.setText("");

        adicionarMensagem(
                "Alex: Interface própria funcionando. "
                + "A conexão com a Ponte Alex v2 será adicionada na próxima etapa."
        );
    }

    private void adicionarMensagem(String texto) {

        TextView mensagem = new TextView(this);

        mensagem.setText(texto);
        mensagem.setTextColor(Color.WHITE);
        mensagem.setTextSize(16);
        mensagem.setPadding(20, 15, 20, 15);

        mensagens.addView(mensagem);
    }

    @Override
    public void onBackPressed() {
        super.onBackPressed();
    }
            }
