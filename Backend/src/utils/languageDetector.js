export function detectLanguage(fileName) {
    if (fileName.endsWith(".java"))  return "java";
    if (fileName.endsWith(".py"))    return "python";
    if (fileName.endsWith(".cpp"))   return "cpp";
    if (fileName.endsWith(".c"))     return "c";
    if (fileName.endsWith(".js"))    return "javascript";
    return "unknown";
}
