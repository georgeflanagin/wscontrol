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
