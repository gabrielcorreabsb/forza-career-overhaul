using System.Text;
using FH6LocalCryptoTool;

static class Program
{
    static int Main(string[] args)
    {
        try
        {
            if (args.Length == 3 && args[0] == "dec")
            {
                var enc = File.ReadAllBytes(args[1]);
                var plain = MotorsportCmsCacheContainer.Decrypt(enc);
                File.WriteAllBytes(args[2], plain);
                Console.WriteLine($"dec ok: {enc.Length} -> {plain.Length}");
                Console.WriteLine("head: " + Encoding.UTF8.GetString(plain, 0, Math.Min(400, plain.Length)));
                return 0;
            }
            if (args.Length == 4 && args[0] == "enc")
            {
                var plain = File.ReadAllBytes(args[1]);
                var tpl = File.ReadAllBytes(args[2]);
                var outBytes = MotorsportCmsCacheContainer.Encrypt(plain, tpl);
                File.WriteAllBytes(args[3], outBytes);
                Console.WriteLine($"enc ok: {plain.Length} -> {outBytes.Length} (template {tpl.Length})");
                return 0;
            }
            Console.Error.WriteLine("usage: cacheoracle dec <enc> <out> | cacheoracle enc <plain> <template> <out>");
            return 2;
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine("ERRO: " + ex.GetType().Name + ": " + ex.Message);
            return 1;
        }
    }
}
