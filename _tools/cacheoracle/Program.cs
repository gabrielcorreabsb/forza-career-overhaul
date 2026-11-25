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
            // gamedb.slt (install, media\base\db): same codec family, own tables.
            // db-enc refuses unless decrypting its own output gives back the input.
            if (args.Length == 3 && args[0] == "db-dec")
            {
                var enc = File.ReadAllBytes(args[1]);
                var sqlite = MotorsportGameDb.Decrypt(enc);
                File.WriteAllBytes(args[2], sqlite);
                Console.WriteLine($"db-dec ok: {enc.Length} -> {sqlite.Length}");
                return 0;
            }
            if (args.Length == 4 && args[0] == "db-enc")
            {
                var sqlite = File.ReadAllBytes(args[1]);
                var tpl = File.ReadAllBytes(args[2]);
                var outBytes = MotorsportGameDb.Encrypt(sqlite, tpl);
                var back = MotorsportGameDb.Decrypt(outBytes);
                if (!back.AsSpan().SequenceEqual(sqlite))
                    throw new InvalidDataException("round trip failed: decrypt(encrypt(x)) != x");
                File.WriteAllBytes(args[3], outBytes);
                Console.WriteLine($"db-enc ok: {sqlite.Length} -> {outBytes.Length} (template {tpl.Length}, round trip verified)");
                return 0;
            }
            Console.Error.WriteLine("usage: cacheoracle dec <enc> <out> | enc <plain> <template> <out> | db-dec <slt> <out.sqlite> | db-enc <sqlite> <template.slt> <out.slt>");
            return 2;
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine("ERRO: " + ex.GetType().Name + ": " + ex.Message);
            return 1;
        }
    }
}
