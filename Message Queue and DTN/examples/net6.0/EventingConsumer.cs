using System.Data;
using System.Text.Json;
using Npgsql;

namespace Example;

public sealed class EventingConsumer : IDisposable
{
    public event MessageHandler OnMessageReceived;
    private readonly NpgsqlDataSource dataSource;
    private NpgsqlConnection listeningConnection;
    public EventingConsumer(string connectionString)
    {
        this.dataSource = NpgsqlDataSource.Create(connectionString);
    }

    public void OpenChannel(string queueName)
    {
        if (listeningConnection is not null)
        {
            return;
        }

        listeningConnection = dataSource.OpenConnection();
        using var transaction = listeningConnection.BeginTransaction();

        listeningConnection.Notification += (sender, args) =>
        {
            if (string.IsNullOrEmpty(args.Payload)) return;
            Task.Run(() =>
            {
                var message = JsonSerializer.Deserialize<Message>(args.Payload);
                if (message is null) return;
                OnMessageReceived?.Invoke(message, () => Ack(message.DeliveryId), (TimeSpan? retryAfter) => Nack(message.DeliveryId, retryAfter));
            });
        };

        using var openChannelCommand = new NpgsqlCommand("mq.open_channel", listeningConnection, transaction)
        {
            CommandType = CommandType.StoredProcedure,
            Parameters = {
                new() { Value = queueName },
                new() { Value = 8 },
            }
        };
        openChannelCommand.ExecuteNonQuery();
        transaction.Commit();
    }
    // Add this method to EventingConsumer class
    private long? currentChannelId = null;

    public void UpdateNetworkStatus(string networkType, int? bandwidth = null)
    {
        if (!currentChannelId.HasValue)
        {
            // Get channel ID
            using var cmd = dataSource.CreateCommand(
                "SELECT channel_id FROM mq.channel WHERE channel_name = @pid"
            );
            cmd.Parameters.Add(new NpgsqlParameter("pid",
                System.Diagnostics.Process.GetCurrentProcess().Id.ToString()));
            var result = cmd.ExecuteScalar();
            if (result != null)
                currentChannelId = (long)result;
        }

        if (currentChannelId.HasValue)
        {
            using var cmd = dataSource.CreateCommand("SELECT mq.update_network_status(@id, @type, @bw)");
            cmd.Parameters.Add(new NpgsqlParameter("id", currentChannelId.Value));
            cmd.Parameters.Add(new NpgsqlParameter("type", networkType));
            cmd.Parameters.Add(new NpgsqlParameter("bw", bandwidth ?? DBNull.Value));
            cmd.ExecuteNonQuery();
        }
    }

    public void Wait()
    {
        listeningConnection?.Wait(3000);
    }

    public void Ack(long deliveryId)
    {
        using var cmd = dataSource.CreateCommand("mq.ack");
        cmd.CommandType = CommandType.StoredProcedure;
        cmd.Parameters.Add(new NpgsqlParameter { Value = deliveryId });
        cmd.ExecuteNonQuery();
    }

    public void Nack(long deliveryId, TimeSpan? retryAfter = default)
    {
        using var cmd = dataSource.CreateCommand("mq.nack");
        cmd.CommandType = CommandType.StoredProcedure;
        cmd.Parameters.Add(new NpgsqlParameter { Value = deliveryId });
        if (retryAfter != default)
        {
            cmd.Parameters.Add(new NpgsqlParameter { Value = retryAfter });
        }
        cmd.ExecuteNonQuery();
    }

    public void CloseChannel()
    {
        if (listeningConnection is null) return;
        Console.WriteLine($"Closing channel");
        using var closeChannelCommand = new NpgsqlCommand("mq.close_channel", listeningConnection)
        {
            CommandType = CommandType.StoredProcedure,
        };
        closeChannelCommand.ExecuteNonQuery();
        listeningConnection.Close();
    }

    public void SweepWaitingMessage(string queueName)
    {
        using var cmd = dataSource.CreateCommand("mq.sweep_waiting_message");
        cmd.CommandType = CommandType.StoredProcedure;
        cmd.Parameters.Add(new NpgsqlParameter { Value = queueName });
        cmd.ExecuteNonQuery();
    }

    public delegate void MessageHandler(Message m, Action ack, Action<TimeSpan?> nack);

    public void Dispose()
    {
        dataSource?.Dispose();
        listeningConnection?.Dispose();
    }
}