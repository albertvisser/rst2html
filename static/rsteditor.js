var editor = CodeMirror.fromTextArea(document.getElementById("rstdata"), {
    lineWrapping: true
});
editor.getInputField().spellcheck = true;
