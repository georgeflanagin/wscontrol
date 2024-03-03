CREATE TABLE master (
    t datetime default current_timestamp,
    who varchar(20),
    host varchar(20),
    command varchar(2000),
    result integer
    );
CREATE TABLE cpu_mem (
        t datetime default current_timestamp,
        host varchar(20),
        cpu_used varchar(20),
        cpu_total varchar(20),
        mem_used varchar(20),
        mem_total varchar(20)
        );
CREATE TABLE IF NOT EXISTS gpu(
        t datetime default current_timestamp,
        host varchar(20),
        gpu_id varchar(20),
        pstate varchar(20),
        powerdraw varchar(20),
        temperature varchar(20),
        fanspeed varchar(20),
        memused varchar(20),
        memtotal varchar(20),
        GPU-Util varchar(20)
        );
