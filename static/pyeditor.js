var editor = CodeMirror.fromTextArea(document.getElementById('rstdata'), {
    mode: {name: "python",
           version: 2,
           singleLineStringErrors: false},
    lineNumbers: true,
    indentUnit: 4,
    matchBrackets: true
});
