// cmsoracle - oráculo .NET para o container criptográfico do CMS do FM8.
// Usa a implementação de referência (FH6LocalCrypto.Runtime.dll do Forza Mod Tool 1.3.0)
// para decriptar/criptar entradas do CMS e validar o codec Python.
//
// uso:
//   cmsoracle dec <entrada.cifrada> <saida.plain>
//   cmsoracle enc <plain> <template.cifrado> <saida.cifrada>
//   cmsoracle hasprefix <entrada.cifrada>
using FH6LocalCryptoTool;

if (args.Length == 0)
{
    Console.Error.WriteLine("uso: cmsoracle dec|enc|hasprefix ...");
    return 2;
}

try
{
    switch (args[0])
    {
        case "dec":
        {
            var enc = File.ReadAllBytes(args[1]);
            var pt = MotorsportCmsContainer.Decrypt(enc);
            File.WriteAllBytes(args[2], pt);
            Console.WriteLine($"OK dec {enc.Length} -> {pt.Length}");
            return 0;
        }
        case "enc":
        {
            var plain = File.ReadAllBytes(args[1]);
            var template = File.ReadAllBytes(args[2]);
            var outBytes = MotorsportCmsContainer.Encrypt(plain, template);
            File.WriteAllBytes(args[3], outBytes);
            Console.WriteLine($"OK enc {plain.Length} -> {outBytes.Length}");
            return 0;
        }
        case "hasprefix":
        {
            var enc = File.ReadAllBytes(args[1]);
            Console.WriteLine(MotorsportCmsContainer.HasPrefix(enc) ? "PREFIX_OK" : "PREFIX_BAD");
            return 0;
        }
        default:
            Console.Error.WriteLine("comando desconhecido: " + args[0]);
            return 2;
    }
}
catch (Exception ex)
{
    Console.Error.WriteLine("ERRO: " + ex.GetType().Name + ": " + ex.Message);
    return 1;
}
