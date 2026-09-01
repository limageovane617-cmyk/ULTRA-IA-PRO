package com.geovani.alexiaultra;

import android.app.Activity;
import android.os.Bundle;
import android.graphics.Color;
import android.view.ViewGroup;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.LinearLayout;
import android.widget.TextView;

public class MainActivity extends Activity {

    private WebView webView;
    private LinearLayout container;
    private TextView statusText;

    private static final String URL =
            "https://ultra-ia-pro-rhyy3g7h9f5tygntsceeif.streamlit.app/";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        try {
            criarTela();
            criarWebView();
        } catch (Exception e) {
            mostrarErro("Erro ao iniciar o aplicativo:\n\n" + e.toString());
        }
    }

    private void criarTela() {

        container = new LinearLayout(this);
        container.setOrientation(LinearLayout.VERTICAL);
        container.setBackgroundColor(Color.WHITE);

        statusText = new TextView(this);
        statusText.setText("Abrindo Alex IA Ultra...");
        statusText.setTextSize(18);
        statusText.setTextColor(Color.DKGRAY);
        statusText.setGravity(17);
        statusText.setPadding(30, 30, 30, 30);

        container.addView(
                statusText,
                new LinearLayout.LayoutParams(
                        ViewGroup.LayoutParams.MATCH_PARENT,
                        ViewGroup.LayoutParams.WRAP_CONTENT
                )
        );

        setContentView(container);
    }

    private void criarWebView() {

        webView = new WebView(this);

        WebSettings settings = webView.getSettings();

        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setDatabaseEnabled(true);
        settings.setLoadWithOverviewMode(true);
        settings.setUseWideViewPort(true);

        webView.setWebViewClient(new WebViewClient() {

            @Override
            public void onPageStarted(
                    WebView view,
                    String url,
                    android.graphics.Bitmap favicon) {

                statusText.setText("Conectando à Alex IA Ultra...");
            }

            @Override
            public void onPageFinished(
                    WebView view,
                    String url) {

                statusText.setVisibility(TextView.GONE);
            }

            @Override
            public void onReceivedError(
                    WebView view,
                    WebResourceRequest request,
                    WebResourceError error) {

                if (request.isForMainFrame()) {
                    mostrarErro(
                            "Não foi possível carregar a Alex IA Ultra.\n\n"
                            + error.getDescription()
                    );
                }
            }

            @Override
            public boolean onRenderProcessGone(
                    WebView view,
                    android.webkit.RenderProcessGoneDetail detail) {

                mostrarErro(
                        "O mecanismo WebView foi encerrado pelo Android.\n\n"
                        + "O aplicativo continuou aberto para mostrar este diagnóstico."
                );

                return true;
            }
        });

        webView.setWebChromeClient(new WebChromeClient());

        container.addView(
                webView,
                new LinearLayout.LayoutParams(
                        ViewGroup.LayoutParams.MATCH_PARENT,
                        0,
                        1
                )
        );

        webView.loadUrl(URL);
    }

    private void mostrarErro(String mensagem) {

        if (statusText != null) {
            statusText.setVisibility(TextView.VISIBLE);
            statusText.setText(mensagem);
        }
    }

    @Override
    public void onBackPressed() {

        if (webView != null && webView.canGoBack()) {
            webView.goBack();
        } else {
            super.onBackPressed();
        }
    }

    @Override
    protected void onDestroy() {

        if (webView != null) {
            webView.stopLoading();
            webView.destroy();
            webView = null;
        }

        super.onDestroy();
    }
}
