package com.geovani.alexiaultra;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Color;
import android.graphics.drawable.GradientDrawable;
import android.net.Uri;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.EditText;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.PopupMenu;
import android.widget.ScrollView;
import android.widget.TextView;
import android.provider.OpenableColumns;
import android.database.Cursor;
import android.os.Build;
import android.provider.Settings;
import android.content.ActivityNotFoundException;

import androidx.core.content.FileProvider;

import java.io.File;
import java.io.FileOutputStream;

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
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;

public class MainActivity extends Activity {

    private LinearLayout tela;
    private LinearLayout mensagens;
    private EditText campoMensagem;
    private EditText campoCodigo;

    // ============================================================
    // ARQUIVO SELECIONADO
    // ============================================================

    private String nomeArquivoSelecionado = "";
    private String conteudoArquivoSelecionado = "";

    private static final int REQUEST_SELECIONAR_ARQUIVO = 1001;

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
        // ÁREA DO CHAT
        // ============================================================

        ScrollView scroll = new ScrollView(this);

        mensagens = new LinearLayout(this);
        mensagens.setOrientation(LinearLayout.VERTICAL);
        mensagens.setPadding(20, 20, 20, 20);

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
        // BOTÃO + DE FERRAMENTAS
        // ============================================================

        Button botaoMais = new Button(this);

        botaoMais.setText("＋");
        botaoMais.setTextSize(22);
        botaoMais.setTextColor(Color.WHITE);

        botaoMais.setOnClickListener(v -> {

            PopupMenu menu =
                    new PopupMenu(
                            MainActivity.this,
                            botaoMais
                    );

            menu.getMenu().add("🖼️ Imagem");
            menu.getMenu().add("🎬 Vídeo");
            menu.getMenu().add("🔊 Voz");
            menu.getMenu().add("💻 Código");
            menu.getMenu().add("📎 Arquivo");
            menu.getMenu().add("🎭 Personagem");
            menu.getMenu().add("🧠 Memória");
            menu.getMenu().add("🗑️ Limpar chat");

            menu.setOnMenuItemClickListener(item -> {

                String ferramenta =
                        item.getTitle().toString();

                // ====================================================
                // 🖼️ IMAGEM
                // ====================================================

                if (ferramenta.equals("🖼️ Imagem")) {

                    campoMensagem.setHint(
                            "Descreva a imagem que você quer criar..."
                    );

                    campoMensagem.requestFocus();

                    adicionarMensagem(
                            "🖼️ Modo Imagem ativado.\n\n"
                                    + "Digite a descrição da imagem "
                                    + "que você quer gerar."
                    );

                    return true;
                }

                // ====================================================
                // 💻 CÓDIGO
                // ====================================================

                if (ferramenta.equals("💻 Código")) {

                    mostrarInterfaceCodigo();

                    return true;
                }

                // ====================================================
                // 📎 ARQUIVO
                // ====================================================

                if (ferramenta.equals("📎 Arquivo")) {

                    abrirSeletorDeArquivo();

                    return true;
                }

                // ====================================================
                // 🗑️ LIMPAR CHAT
                // ====================================================

                if (ferramenta.equals("🗑️ Limpar chat")) {

                    mensagens.removeAllViews();

                    adicionarMensagem(
                            "🗑️ Chat limpo."
                    );

                    return true;
                }

                // ====================================================
                // OUTRAS FERRAMENTAS
                // ====================================================

                adicionarMensagem(
                        "🧰 Ferramenta selecionada: "
                                + ferramenta
                );

                return true;
            });

            menu.show();
        });

        // ============================================================
        // ÁREA DE DIGITAÇÃO
        // ============================================================

        LinearLayout entrada =
                new LinearLayout(this);

        entrada.setOrientation(
                LinearLayout.HORIZONTAL
        );

        entrada.setGravity(
                Gravity.CENTER_VERTICAL
        );

        GradientDrawable fundoEntrada =
                new GradientDrawable();

        fundoEntrada.setColor(
                Color.rgb(20, 26, 38)
        );

        fundoEntrada.setCornerRadius(
                80f
        );

        entrada.setBackground(
                fundoEntrada
        );

        entrada.setPadding(
                12,
                6,
                8,
                6
        );

        // ============================================================
        // BOTÃO +
        // ============================================================

        botaoMais.setBackgroundColor(
                Color.TRANSPARENT
        );

        botaoMais.setMinWidth(0);
        botaoMais.setMinimumWidth(0);

        botaoMais.setPadding(
                6,
                0,
                6,
                0
        );

        botaoMais.setText("＋");
        botaoMais.setTextSize(24);
        botaoMais.setTextColor(Color.WHITE);

        entrada.addView(
                botaoMais,
                new LinearLayout.LayoutParams(
                        ViewGroup.LayoutParams.WRAP_CONTENT,
                        ViewGroup.LayoutParams.MATCH_PARENT
                )
        );

        // ============================================================
        // CAMPO DE MENSAGEM
        // ============================================================

        campoMensagem =
                new EditText(this);

        campoMensagem.setHint(
                "Digite sua mensagem..."
        );

        campoMensagem.setHintTextColor(
                Color.LTGRAY
        );

        campoMensagem.setTextColor(
                Color.WHITE
        );

        campoMensagem.setTextSize(16);

        campoMensagem.setSingleLine(true);

        campoMensagem.setBackgroundColor(
                Color.TRANSPARENT
        );

        campoMensagem.setPadding(
                8,
                0,
                8,
                0
        );

        entrada.addView(
                campoMensagem,
                new LinearLayout.LayoutParams(
                        0,
                        ViewGroup.LayoutParams.MATCH_PARENT,
                        1
                )
        );

        // ============================================================
        // BOTÃO ENVIAR
        // ============================================================

        Button enviar =
                new Button(this);

        enviar.setText("🚀");
        enviar.setTextSize(20);
        enviar.setTextColor(Color.WHITE);

        enviar.setBackgroundColor(
                Color.TRANSPARENT
        );

        enviar.setMinWidth(0);
        enviar.setMinimumWidth(0);

        enviar.setPadding(
                6,
                0,
                4,
                0
        );

        enviar.setOnClickListener(
                v -> enviarMensagem()
        );

        entrada.addView(
                enviar,
                new LinearLayout.LayoutParams(
                        ViewGroup.LayoutParams.WRAP_CONTENT,
                        ViewGroup.LayoutParams.MATCH_PARENT
                )
        );

        // ============================================================
        // COLOCAR O BALÃO NA TELA
        // ============================================================

        float densidade =
                getResources()
                        .getDisplayMetrics()
                        .density;

        LinearLayout.LayoutParams parametrosEntrada =
                new LinearLayout.LayoutParams(
                        ViewGroup.LayoutParams.MATCH_PARENT,
                        (int) (58 * densidade)
                );

        parametrosEntrada.setMargins(
                (int) (12 * densidade),
                (int) (8 * densidade),
                (int) (12 * densidade),
                (int) (12 * densidade)
        );

        tela.addView(
                entrada,
                parametrosEntrada
        );

        setContentView(tela);
    }

    // ============================================================
    // INTERFACE DE CÓDIGO
    // ============================================================

    private void mostrarInterfaceCodigo() {

        LinearLayout layout =
                new LinearLayout(this);

        layout.setOrientation(
                LinearLayout.VERTICAL
        );

        layout.setPadding(
                30,
                20,
                30,
                10
        );

        campoCodigo =
                new EditText(this);

        campoCodigo.setHint(
                "Cole aqui o código..."
        );

        campoCodigo.setHintTextColor(
                Color.LTGRAY
        );

        campoCodigo.setTextColor(
                Color.WHITE
        );

        campoCodigo.setTextSize(15);

        campoCodigo.setGravity(
                Gravity.TOP
        );

        campoCodigo.setMinLines(8);

        campoCodigo.setPadding(
                15,
                15,
                15,
                15
        );

        GradientDrawable fundoCodigo =
                new GradientDrawable();

        fundoCodigo.setColor(
                Color.rgb(20, 26, 38)
        );

        fundoCodigo.setCornerRadius(
                25f
        );

        campoCodigo.setBackground(
                fundoCodigo
        );

        layout.addView(
                campoCodigo,
                new LinearLayout.LayoutParams(
                        ViewGroup.LayoutParams.MATCH_PARENT,
                        0,
                        1
                )
        );

        EditText campoInstrucao =
                new EditText(this);

        campoInstrucao.setHint(
                "O que a Ponte deve fazer?"
        );

        campoInstrucao.setHintTextColor(
                Color.LTGRAY
        );

        campoInstrucao.setTextColor(
                Color.WHITE
        );

        campoInstrucao.setTextSize(15);

        campoInstrucao.setPadding(
                15,
                15,
                15,
                15
        );

        GradientDrawable fundoInstrucao =
                new GradientDrawable();

        fundoInstrucao.setColor(
                Color.rgb(20, 26, 38)
        );

        fundoInstrucao.setCornerRadius(
                25f
        );

        campoInstrucao.setBackground(
                fundoInstrucao
        );

        LinearLayout.LayoutParams parametrosInstrucao =
                new LinearLayout.LayoutParams(
                        ViewGroup.LayoutParams.MATCH_PARENT,
                        ViewGroup.LayoutParams.WRAP_CONTENT
                );

        parametrosInstrucao.setMargins(
                0,
                12,
                0,
                0
        );

        layout.addView(
                campoInstrucao,
                parametrosInstrucao
        );

        AlertDialog dialog =
                new AlertDialog.Builder(this)
                        .setTitle("💻 Código")
                        .setView(layout)
                        .setNegativeButton(
                                "Cancelar",
                                null
                        )
                        .setPositiveButton(
                                "🌉 Processar",
                                null
                        )
                        .create();

        dialog.setOnShowListener(
                dialogInterface -> {

                    Button botaoProcessar =
                            dialog.getButton(
                                    AlertDialog.BUTTON_POSITIVE
                            );

                    botaoProcessar.setOnClickListener(
                            v -> {

                                String codigo =
                                        campoCodigo
                                                .getText()
                                                .toString();

                                String instrucao =
                                        campoInstrucao
                                                .getText()
                                                .toString();

                                processarPelaPonte(
                                        codigo,
                                        instrucao
                                );

                                dialog.dismiss();
                            }
                    );
                }
        );

        dialog.show();
    }

    // ============================================================
    // ABRIR SELETOR DE ARQUIVO
    // ============================================================

    private void abrirSeletorDeArquivo() {

        Intent intent =
                new Intent(
                        Intent.ACTION_OPEN_DOCUMENT
                );

        intent.addCategory(
                Intent.CATEGORY_OPENABLE
        );

        intent.setType("*/*");

        startActivityForResult(
                intent,
                REQUEST_SELECIONAR_ARQUIVO
        );
    }

    // ============================================================
    // RESULTADO DO SELETOR DE ARQUIVO
    // ============================================================

    @Override
    protected void onActivityResult(
            int requestCode,
            int resultCode,
            Intent data
    ) {

        super.onActivityResult(
                requestCode,
                resultCode,
                data
        );

        if (
                requestCode
                        != REQUEST_SELECIONAR_ARQUIVO
                        || resultCode
                        != RESULT_OK
                        || data == null
                        || data.getData() == null
        ) {

            return;
        }

        Uri uri = data.getData();

        lerArquivoSelecionado(uri);
    }

    // ============================================================
    // LER ARQUIVO
    // ============================================================

    private void lerArquivoSelecionado(
            Uri uri
    ) {

        executor.execute(() -> {

            try {

                String nome =
                        obterNomeArquivo(uri);

                if (
                        nome == null
                                || nome.isEmpty()
                ) {

                    nome =
                            "arquivo_selecionado";
                }

                final String nomeFinal =
                        nome;

                // ========================================================
                // ZIP
                // ========================================================

                if (
                        nome.toLowerCase()
                                .endsWith(".zip")
                ) {

                    List<String> arquivosZip =
                            listarArquivosZip(uri);

                    boolean encontrouApk =
                            false;

                    for (
                            String arquivo :
                            arquivosZip
                    ) {

                        if (
                                arquivo
                                        .toLowerCase()
                                        .endsWith(".apk")
                        ) {

                            encontrouApk =
                                    true;

                            break;
                        }
                    }

                    final boolean apkEncontrado =
                            encontrouApk;

                    runOnUiThread(() -> {

                        if (
                                arquivosZip.isEmpty()
                        ) {

                            adicionarMensagem(
                                    "📦 ZIP carregado: "
                                            + nomeFinal
                                            + "\n"
                                            + "Nenhum arquivo encontrado dentro do ZIP."
                            );

                            return;
                        }

                        StringBuilder lista =
                                new StringBuilder();

                        lista.append(
                                "📦 ZIP carregado: "
                        );

                        lista.append(
                                nomeFinal
                        );

                        lista.append(
                                "\n\nArquivos encontrados:"
                        );

                        for (
                                String arquivo :
                                arquivosZip
                        ) {

                            lista.append(
                                    "\n📄 "
                            );

                            lista.append(
                                    arquivo
                            );
                        }

                        if (
                                apkEncontrado
                        ) {

                            lista.append(
                                    "\n\n📱 APK encontrado dentro do ZIP!"
                            );

                            lista.append(
                                    "\n📱 Pronto para instalar."
                            );

                        } else {

                            lista.append(
                                    "\n\n📦 Nenhum APK encontrado dentro do ZIP."
                            );
                        }

                        adicionarMensagem(
                                lista.toString()
                        );
                    });

                    // ========================================================
                    // INSTALAR APK ENCONTRADO
                    // ========================================================

                    if (
                            apkEncontrado
                    ) {

                        runOnUiThread(() -> {

                            Button botaoInstalar =
                                    new Button(this);

                            botaoInstalar.setText(
                                    "📱 Instalar APK"
                            );

                            botaoInstalar.setOnClickListener(
                                    v -> {

                                        executor.execute(() -> {

                                            try {

                                                extrairEInstalarApk(
                                                        uri
                                                );

                                            } catch (
                                                    Exception erro
                                            ) {

                                                runOnUiThread(() -> {

                                                    adicionarMensagem(
                                                            "📱 Não foi possível instalar o APK: "
                                                                    + erro.getMessage()
                                                    );
                                                });
                                            }
                                        });
                                    }
                            );

                            mensagens.addView(
                                    botaoInstalar
                            );
                        });
                    }

                    return;
                }

                // ========================================================
                // APK DIRETO
                // ========================================================

                if (
                        nomeFinal
                                .toLowerCase()
                                .endsWith(".apk")
                ) {

                    File apkFile =
                            new File(
                                    getCacheDir(),
                                    "apk_direto_instalacao.apk"
                            );

                    InputStream entradaApk =
                            getContentResolver()
                                    .openInputStream(uri);

                    if (
                            entradaApk == null
                    ) {

                        throw new Exception(
                                "Não foi possível abrir o APK."
                        );
                    }

                    FileOutputStream saidaApk =
                            new FileOutputStream(
                                    apkFile
                            );

                    byte[] bufferApk =
                            new byte[8192];

                    int quantidadeApk;

                    while (
                            (quantidadeApk =
                                    entradaApk.read(
                                            bufferApk
                                    ))
                                    != -1
                    ) {

                        saidaApk.write(
                                bufferApk,
                                0,
                                quantidadeApk
                        );
                    }

                    saidaApk.flush();
                    saidaApk.close();
                    entradaApk.close();

                    runOnUiThread(() -> {

                        adicionarMensagem(
                                "📱 APK carregado: "
                                        + nomeFinal
                                        + "\n\n"
                                        + "O APK foi reconhecido corretamente."
                                        + "\n"
                                        + "Ele não será lido como texto."
                        );

                        Button botaoInstalar =
                                new Button(this);

                        botaoInstalar.setText(
                                "📱 Instalar APK"
                        );

                        botaoInstalar.setOnClickListener(
                                v -> abrirInstaladorApk(
                                        apkFile
                                )
                        );

                        mensagens.addView(
                                botaoInstalar
                        );
                    });

                    return;
                }

                // ========================================================
                // ARQUIVO DE TEXTO
                // ========================================================

                String conteudo =
                        lerConteudoArquivo(uri);

                nomeArquivoSelecionado =
                        nomeFinal;

                conteudoArquivoSelecionado =
                        conteudo;

                runOnUiThread(() -> {

                    adicionarMensagem(
                            "📎 Arquivo carregado: "
                                    + nomeArquivoSelecionado
                                    + "\n"
                                    + "Tamanho: "
                                    + conteudoArquivoSelecionado.length()
                                    + " caracteres."
                    );

                    adicionarMensagem(
                            "📎 Arquivo pronto para a próxima etapa."
                    );
                });

                return;

            } catch (
                    Exception erro
            ) {

                runOnUiThread(() -> {

                    adicionarMensagem(
                            "📎 Erro ao ler o arquivo: "
                                    + erro.getMessage()
                    );
                });
            }
        });
    }

    // ============================================================
    // LISTAR ARQUIVOS DO ZIP
    // ============================================================

    private List<String> listarArquivosZip(
            Uri uri
    ) throws Exception {

        List<String> arquivos =
                new ArrayList<>();

        InputStream entrada =
                getContentResolver()
                        .openInputStream(uri);

        if (
                entrada == null
        ) {

            throw new Exception(
                    "Não foi possível abrir o ZIP."
            );
        }

        ZipInputStream zip =
                new ZipInputStream(
                        entrada
                );

        ZipEntry entradaZip;

        while (
                (entradaZip =
                        zip.getNextEntry())
                        != null
        ) {

            if (
                    !entradaZip.isDirectory()
            ) {

                arquivos.add(
                        entradaZip.getName()
                );
            }

            zip.closeEntry();
        }

        zip.close();
        entrada.close();

        return arquivos;
    }

    // ============================================================
    // EXTRAIR E INSTALAR APK
    // ============================================================

    private void extrairEInstalarApk(
            Uri uri
    ) throws Exception {

        InputStream entrada =
                getContentResolver()
                        .openInputStream(uri);

        if (
                entrada == null
        ) {

            throw new Exception(
                    "Não foi possível abrir o ZIP."
            );
        }

        ZipInputStream zip =
                new ZipInputStream(
                        entrada
                );

        ZipEntry entradaZip;

        while (
                (entradaZip =
                        zip.getNextEntry())
                        != null
        ) {

            if (
                    !entradaZip.isDirectory()
                            &&
                    entradaZip.getName()
                            .toLowerCase()
                            .endsWith(".apk")
            ) {

                File apkFile =
                        new File(
                                getCacheDir(),
                                "apk_instalacao.apk"
                        );

                FileOutputStream saida =
                        new FileOutputStream(
                                apkFile
                        );

                byte[] buffer =
                        new byte[8192];

                int quantidade;

                while (
                        (quantidade =
                                zip.read(buffer))
                                != -1
                ) {

                    saida.write(
                            buffer,
                            0,
                            quantidade
                    );
                }

                saida.flush();
                saida.close();

                zip.closeEntry();
                zip.close();
                entrada.close();

                abrirInstaladorApk(
                        apkFile
                );

                return;
            }

            zip.closeEntry();
        }

        zip.close();
        entrada.close();

        throw new Exception(
                "Nenhum APK foi encontrado dentro do ZIP."
        );
    }

    // ============================================================
    // ABRIR INSTALADOR DO APK
    // ============================================================

    private void abrirInstaladorApk(
            File apkFile
    ) {

        try {

            if (
                    Build.VERSION.SDK_INT
                            >= Build.VERSION_CODES.O
            ) {

                if (
                        !getPackageManager()
                                .canRequestPackageInstalls()
                ) {

                    Intent configuracao =
                            new Intent(
                                    Settings
                                            .ACTION_MANAGE_UNKNOWN_APP_SOURCES,
                                    Uri.parse(
                                            "package:"
                                                    + getPackageName()
                                    )
                            );

                    startActivity(
                            configuracao
                    );

                    adicionarMensagem(
                            "📱 Permita a instalação deste aplicativo e depois tente instalar o APK novamente."
                    );

                    return;
                }
            }

            Uri apkUri =
                    FileProvider.getUriForFile(
                            this,
                            getPackageName()
                                    + ".fileprovider",
                            apkFile
                    );

            Intent instalador =
                    new Intent(
                            Intent.ACTION_VIEW
                    );

            instalador.setDataAndType(
                    apkUri,
                    "application/vnd.android.package-archive"
            );

            instalador.addFlags(
                    Intent.FLAG_GRANT_READ_URI_PERMISSION
            );

            instalador.addFlags(
                    Intent.FLAG_ACTIVITY_NEW_TASK
            );

            startActivity(
                    instalador
            );

        } catch (
                ActivityNotFoundException erro
        ) {

            adicionarMensagem(
                    "📱 Não foi possível abrir o instalador do APK."
            );

        } catch (
                Exception erro
        ) {

            adicionarMensagem(
                    "📱 Erro ao abrir o APK: "
                            + erro.getMessage()
            );
        }
    }

    // ============================================================
    // OBTER NOME DO ARQUIVO
    // ============================================================

    private String obterNomeArquivo(
            Uri uri
    ) {

        Cursor cursor = null;

        try {

            cursor =
                    getContentResolver().query(
                            uri,
                            null,
                            null,
                            null,
                            null
                    );

            if (
                    cursor != null
                            && cursor.moveToFirst()
            ) {

                int indice =
                        cursor.getColumnIndex(
                                OpenableColumns.DISPLAY_NAME
                        );

                if (
                        indice >= 0
                ) {

                    return cursor.getString(
                            indice
                    );
                }
            }

        } finally {

            if (
                    cursor != null
            ) {

                cursor.close();
            }
        }

        return "";
    }

    // ============================================================
    // LER CONTEÚDO UTF-8
    // ============================================================

    private String lerConteudoArquivo(
            Uri uri
    ) throws Exception {

        InputStream entrada =
                getContentResolver()
                        .openInputStream(uri);

        if (
                entrada == null
        ) {

            throw new Exception(
                    "Não foi possível abrir o arquivo."
            );
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

        while (
                (linha = leitor.readLine())
                        != null
        ) {

            resultado
                    .append(linha)
                    .append("\n");
        }

        leitor.close();
        entrada.close();

        return resultado.toString();
    }

    // ============================================================
    // ENVIAR MENSAGEM PARA A API
    // ============================================================

    private void enviarMensagem() {

        String texto =
                campoMensagem
                        .getText()
                        .toString()
                        .trim();

        if (
                texto.isEmpty()
        ) {

            return;
        }

        adicionarMensagem(
                "Você: " + texto
        );

        campoMensagem.setText("");

        adicionarMensagem(
                "Alex: pensando..."
        );

        executor.execute(() -> {

            HttpURLConnection connection =
                    null;

            try {

                JSONObject pedido =
                        new JSONObject();

                pedido.put(
                        "pergunta",
                        texto
                );

                JSONArray arrayHistorico =
                        new JSONArray();

                for (
                        JSONObject item :
                        historico
                ) {

                    arrayHistorico.put(
                            item
                    );
                }

                pedido.put(
                        "historico",
                        arrayHistorico
                );

                pedido.put(
                        "contexto_arquivo",
                        conteudoArquivoSelecionado
                );

                pedido.put(
                        "nome_arquivo",
                        nomeArquivoSelecionado
                );

                URL url =
                        new URL(
                                API_URL
                        );

                connection =
                        (HttpURLConnection)
                                url.openConnection();

                connection.setRequestMethod(
                        "POST"
                );

                connection.setRequestProperty(
                        "Content-Type",
                        "application/json; charset=UTF-8"
                );

                connection.setRequestProperty(
                        "Accept",
                        "application/json"
                );

                connection.setDoOutput(
                        true
                );

                connection.setConnectTimeout(
                        30000
                );

                connection.setReadTimeout(
                        60000
                );

                byte[] dados =
                        pedido
                                .toString()
                                .getBytes(
                                        StandardCharsets.UTF_8
                                );

                OutputStream saida =
                        connection
                                .getOutputStream();

                saida.write(
                        dados
                );

                saida.flush();
                saida.close();

                int responseCode =
                        connection
                                .getResponseCode();

                InputStream entradaResposta;

                if (
                        responseCode >= 200
                                && responseCode < 300
                ) {

                    entradaResposta =
                            connection
                                    .getInputStream();

                } else {

                    entradaResposta =
                            connection
                                    .getErrorStream();
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

                String tipo =
                        resposta.optString(
                                "tipo",
                                ""
                        );

                // ========================================================
                // RESPOSTA DE IMAGEM
                // ========================================================

                if (
                        sucesso
                                && tipo.equalsIgnoreCase(
                                        "imagem"
                                )
                ) {

                    String imagem =
                            resposta.optString(
                                    "imagem",
                                    ""
                            );

                    runOnUiThread(() -> {

                        removerMensagemPensando();

                        adicionarMensagem(
                                "Alex: Imagem gerada com sucesso."
                        );

                        if (
                                !imagem.isEmpty()
                        ) {

                            adicionarImagemNaTela(
                                    imagem
                            );
                        }
                    });

                    return;
                }

                // ========================================================
                // RESPOSTA NORMAL
                // ========================================================

                String respostaAlex =
                        resposta.optString(
                                "resposta",
                                "Não consegui obter uma resposta."
                        );

                if (
                        sucesso
                ) {

                    historico.add(
                            new JSONObject()
                                    .put(
                                            "role",
                                            "user"
                                    )
                                    .put(
                                            "content",
                                            texto
                                    )
                    );

                    historico.add(
                            new JSONObject()
                                    .put(
                                            "role",
                                            "model"
                                    )
                                    .put(
                                            "content",
                                            respostaAlex
                                    )
                    );
                }

                runOnUiThread(() -> {

                    removerMensagemPensando();

                    adicionarMensagem(
                            "Alex: "
                                    + respostaAlex
                    );
                });

            } catch (
                    Exception erro
            ) {

                runOnUiThread(() -> {

                    removerMensagemPensando();

                    adicionarMensagem(
                            "Alex: Não consegui conectar "
                                    + "ao servidor agora."
                    );
                });

            } finally {

                if (
                        connection != null
                ) {

                    connection.disconnect();
                }
            }
        });
    }

    // ============================================================
    // LER RESPOSTA DO SERVIDOR
    // ============================================================

    private String lerResposta(
            InputStream entrada
    ) throws Exception {

        if (
                entrada == null
        ) {

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

        while (
                (linha = leitor.readLine())
                        != null
        ) {

            resultado.append(
                    linha
            );
        }

        leitor.close();

        return resultado.toString();
    }

    // ============================================================
    // ADICIONAR IMAGEM NA TELA
    // ============================================================

    private void adicionarImagemNaTela(
            String imagem
    ) {

        if (
                imagem == null
                        || imagem.trim().isEmpty()
        ) {

            return;
        }

        executor.execute(() -> {

            HttpURLConnection conexaoImagem =
                    null;

            try {

                String urlImagem =
                        imagem.trim();

                if (
                        !urlImagem.startsWith(
                                "http://"
                        )
                        &&
                        !urlImagem.startsWith(
                                "https://"
                        )
                ) {

                    urlImagem =
                            "https://ultra-ia-pro.onrender.com"
                                    + (
                                        urlImagem.startsWith("/")
                                                ? urlImagem
                                                : "/" + urlImagem
                                    );
                }

                URL url =
                        new URL(
                                urlImagem
                        );

                conexaoImagem =
                        (HttpURLConnection)
                                url.openConnection();

                conexaoImagem.setRequestMethod(
                        "GET"
                );

                conexaoImagem.setConnectTimeout(
                        30000
                );

                conexaoImagem.setReadTimeout(
                        60000
                );

                conexaoImagem.connect();

                int codigo =
                        conexaoImagem
                                .getResponseCode();

                if (
                        codigo < 200
                                || codigo >= 300
                ) {

                    throw new Exception(
                            "Servidor de imagem respondeu HTTP "
                                    + codigo
                    );
                }

                InputStream entrada =
                        conexaoImagem
                                .getInputStream();

                Bitmap bitmap =
                        BitmapFactory
                                .decodeStream(
                                        entrada
                                );

                entrada.close();

                if (
                        bitmap == null
                ) {

                    throw new Exception(
                            "Não foi possível decodificar a imagem."
                    );
                }

                runOnUiThread(() -> {

                    ImageView imagemView =
                            new ImageView(
                                    MainActivity.this
                            );

                    imagemView.setImageBitmap(
                            bitmap
                    );

                    imagemView.setAdjustViewBounds(
                            true
                    );

                    imagemView.setScaleType(
                            ImageView.ScaleType
                                    .FIT_CENTER
                    );

                    LinearLayout.LayoutParams parametros =
                            new LinearLayout.LayoutParams(
                                    ViewGroup.LayoutParams.MATCH_PARENT,
                                    ViewGroup.LayoutParams.WRAP_CONTENT
                            );

                    parametros.setMargins(
                            20,
                            10,
                            20,
                            20
                    );

                    mensagens.addView(
                            imagemView,
                            parametros
                    );
                });

            } catch (
                    Exception erro
            ) {

                runOnUiThread(() -> {

                    adicionarMensagem(
                            "🖼️ Não foi possível carregar a imagem: "
                                    + erro.getMessage()
                    );
                });

            } finally {

                if (
                        conexaoImagem != null
                ) {

                    conexaoImagem.disconnect();
                }
            }
        });
    }

    // ============================================================
    // PROCESSAR CÓDIGO PELA PONTE ALEX V2
    // ============================================================

    private void processarPelaPonte(
            String codigo,
            String instrucao
    ) {

        codigo =
                codigo.trim();

        instrucao =
                instrucao.trim();

        if (
                codigo.isEmpty()
        ) {

            adicionarMensagem(
                    "Ponte: cole um código para processar."
            );

            return;
        }

        if (
                instrucao.isEmpty()
        ) {

            adicionarMensagem(
                    "Ponte: informe o que deseja modificar."
            );

            return;
        }

        adicionarMensagem(
                "Você → Ponte: processando..."
        );

        final String codigoFinal =
                codigo;

        final String instrucaoFinal =
                instrucao;

        executor.execute(() -> {

            HttpURLConnection conexao =
                    null;

            try {

                JSONObject pedido =
                        new JSONObject();

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
                        new URL(
                                PONTE_API_URL
                        );

                conexao =
                        (HttpURLConnection)
                                url.openConnection();

                conexao.setRequestMethod(
                        "POST"
                );

                conexao.setRequestProperty(
                        "Content-Type",
                        "application/json"
                );

                conexao.setRequestProperty(
                        "Accept",
                        "application/json"
                );

                conexao.setDoOutput(
                        true
                );

                conexao.setConnectTimeout(
                        30000
                );

                conexao.setReadTimeout(
                        90000
                );

                byte[] dados =
                        pedido
                                .toString()
                                .getBytes(
                                        StandardCharsets.UTF_8
                                );

                try (
                        OutputStream saida =
                                conexao.getOutputStream()
                ) {

                    saida.write(
                            dados
                    );
                }

                int codigoHttp =
                        conexao
                                .getResponseCode();

                InputStream entradaResposta;

                if (
                        codigoHttp >= 200
                                && codigoHttp < 300
                ) {

                    entradaResposta =
                            conexao
                                    .getInputStream();

                } else {

                    entradaResposta =
                            conexao
                                    .getErrorStream();
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

                if (
                        sucesso
                ) {

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
                                "Ponte: "
                                        + status
                                        + "\nArquivo processado: "
                                        + nomeArquivo
                        );

                        if (
                                !download.isEmpty()
                        ) {

                            Button botaoDownload =
                                    new Button(this);

                            botaoDownload.setText(
                                    "📥 Baixar arquivo processado"
                            );

                            botaoDownload.setOnClickListener(
                                    v -> {

                                        try {

                                            String urlDownload =
                                                    download;

                                            if (
                                                    !urlDownload
                                                            .startsWith(
                                                                    "http://"
                                                            )
                                                            &&
                                                    !urlDownload
                                                            .startsWith(
                                                                    "https://"
                                                            )
                                            ) {

                                                urlDownload =
                                                        "https://ponte-alex-v2.onrender.com"
                                                                + (
                                                                    urlDownload
                                                                            .startsWith(
                                                                                    "/"
                                                                            )
                                                                            ? urlDownload
                                                                            : "/" + urlDownload
                                                                );
                                            }

                                            Intent navegador =
                                                    new Intent(
                                                            Intent.ACTION_VIEW,
                                                            Uri.parse(
                                                                    urlDownload
                                                            )
                                                    );

                                            startActivity(
                                                    navegador
                                            );

                                        } catch (
                                                Exception erro
                                        ) {

                                            adicionarMensagem(
                                                    "📥 Não foi possível abrir o download: "
                                                            + erro.getMessage()
                                            );
                                        }
                                    }
                            );

                            mensagens.addView(
                                    botaoDownload,
                                    new LinearLayout.LayoutParams(
                                            ViewGroup.LayoutParams.MATCH_PARENT,
                                            ViewGroup.LayoutParams.WRAP_CONTENT
                                    )
                            );
                        }
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
                                "Ponte: "
                                        + erro
                        );
                    });
                }

            } catch (
                    Exception erro
            ) {

                runOnUiThread(() -> {

                    adicionarMensagem(
                            "Ponte: não foi possível "
                                    + "conectar ao servidor."
                    );
                });

            } finally {

                if (
                        conexao != null
                ) {

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

        if (
                quantidade == 0
        ) {

            return;
        }

        View ultima =
                mensagens.getChildAt(
                        quantidade - 1
                );

        if (
                ultima instanceof TextView
        ) {

            TextView texto =
                    (TextView) ultima;

            String valor =
                    texto.getText()
                            .toString();

            if (
                    valor.equals(
                            "Alex: pensando..."
                    )
            ) {

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

        mensagem.setText(
                texto
        );

        mensagem.setTextColor(
                Color.WHITE
        );

        mensagem.setTextSize(
                16
        );

        mensagem.setPadding(
                20,
                15,
                20,
                15
        );

        mensagens.addView(
                mensagem
        );
    }

    // ============================================================
    // DESTRUIR ACTIVITY
    // ============================================================

    @Override
    protected void onDestroy() {

        executor.shutdownNow();

        super.onDestroy();
    }

    // ============================================================
    // BOTÃO VOLTAR
    // ============================================================

    @Override
    public void onBackPressed() {

        super.onBackPressed();
    }
   }
